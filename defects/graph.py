"""
The defect triage workflow as a LangGraph state machine.

    load_context -> classify -> retrieve -> propose -> review -> apply -> notify

`review` is the human-in-the-loop gate: it calls interrupt() and waits for the administrator. It has no side
effects, because on resume the node re-runs from its start - everything that must survive the pause lives in
the checkpointer (the state) or in the DefectTriage row. `apply` is the only node that changes production data:
one transaction.atomic() block, idempotent - if the triage is already applied it returns without doing anything.
"""
import logging
from enum import StrEnum
from typing import TypedDict

from django.db import transaction
from django.utils import timezone
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from defects.models import DefectCase, DefectTriage
from defects.triage.case_service import add_case, get_precedents
from defects.triage.classify import classify_defect
from defects.triage.propose import propose_redo
from llm.exceptions import LlmError
from operations.models import Operation, OperationStatus

logger = logging.getLogger(__name__)

# How many times the administrator can send the proposal back before the workflow gives up and goes manual.
MAX_REVISIONS = 2


class Node(StrEnum):
    """Names of the graph nodes: one spelling for add_node, the edges and the routing functions."""

    LOAD_CONTEXT = "load_context"
    CLASSIFY = "classify"
    RETRIEVE = "retrieve"
    PROPOSE = "propose"
    REVIEW = "review"
    APPLY = "apply"
    NOTIFY = "notify"


class TriageState(TypedDict, total=False):
    triage_id: str
    comment: str
    work_names: list[str]
    classification: dict  # DefectClassification.model_dump(), absent when classification failed
    precedents: list[str]
    proposal: dict  # operation_id/name, likely_cause, recommendation; absent in manual review
    manual: bool  # True: review with no proposal, the administrator decides everything
    error: str  # why the workflow went manual, if it did
    revisions: int  # mirror of DefectTriage.revisions, for routing
    decision: dict  # what the administrator answered on resume: action, note, final, decided_by_id
    notified: bool


def load_context(state: TriageState) -> TriageState:
    triage = _triage(state)
    triage.state = DefectTriage.State.PROCESSING
    triage.save(update_fields=["state", "updated_at"])
    works = list(triage.works.select_related("work_type"))
    return {
        "comment": triage.comment,
        "work_names": [work.work_type.name for work in works],
        "revisions": triage.revisions,
    }


def classify_node(state: TriageState) -> TriageState:
    triage = _triage(state)
    try:
        result = classify_defect(state["work_names"], state["comment"], user=triage.reported_by)
    except LlmError as exc:
        return {"manual": True, "error": f"classification failed: {exc}"}
    classification = result.model_dump()
    if classification["confidence"] == "low":
        # A vague report must not reach the propose step: the administrator classifies it by hand.
        return {"manual": True, "classification": classification, "error": "classification confidence is low"}
    return {"classification": classification}


def retrieve_node(state: TriageState) -> TriageState:
    try:
        precedents = get_precedents(state["classification"]["description"])
    except Exception as exc:  # embeddings or the database: without precedents there is still a proposal to review
        return {"manual": True, "error": f"precedent retrieval failed: {exc}"}
    return {"precedents": precedents}


def propose_node(state: TriageState) -> TriageState:
    triage = _triage(state)
    feedback = ""
    decision = state.get("decision")
    if decision and decision.get("action") == DefectTriage.Decision.REJECT:
        if state.get("revisions", 0) >= MAX_REVISIONS:
            return {"manual": True, "proposal": None, "error": "revision limit reached"}
        triage.revisions += 1
        triage.save(update_fields=["revisions", "updated_at"])
        feedback = decision.get("note", "")

    try:
        redo = propose_redo(
            triage.works.all(),
            state["classification"]["description"],
            state["classification"]["defect_type"],
            state["classification"]["severity"],
            feedback=feedback,
            precedents=state.get("precedents"),
            user=triage.reported_by,
        )
    except LlmError as exc:
        return {"manual": True, "proposal": None, "error": f"proposal failed: {exc}"}

    proposal = {
        "operation_id": str(redo.operation.id),
        "operation_name": redo.operation.operation_type.name,
        "likely_cause": redo.proposal.likely_cause,
        "recommendation": redo.proposal.recommendation,
    }
    triage.proposal = proposal
    triage.state = DefectTriage.State.AWAITING_REVIEW
    triage.save(update_fields=["proposal", "state", "updated_at"])
    return {"proposal": proposal, "manual": False, "revisions": triage.revisions}


def review_node(state: TriageState) -> TriageState:
    """Ask the administrator. The only thing this node does is interrupt(); no DB writes, no sends."""
    decision = interrupt({
        "triage_id": state["triage_id"],
        "manual": state.get("manual", False),
        "error": state.get("error", ""),
        "classification": state.get("classification"),
        "proposal": state.get("proposal"),
        "revisions": state.get("revisions", 0),
        "max_revisions": MAX_REVISIONS,
    })
    if decision.get("action") not in DefectTriage.Decision.values:
        raise ValueError(f"unknown review action {decision.get('action')!r}")
    return {"decision": decision}


def apply_node(state: TriageState) -> TriageState:
    """
    Write the administrator's decision. One transaction, idempotent: if the triage is already applied (or
    closed) the node returns without touching anything, so a replayed graph run cannot reset the operation twice.
    """
    decision = state["decision"]
    with transaction.atomic():
        triage = DefectTriage.objects.select_for_update().get(id=state["triage_id"])
        if triage.state == DefectTriage.State.APPLIED or triage.applied_at:
            return {}

        triage.decision = decision["action"]
        triage.decision_note = decision.get("note", "")[:500]
        triage.decided_by_id = decision.get("decided_by_id")
        triage.decided_at = timezone.now()
        triage.final = decision.get("final", {})

        action = decision["action"]
        if action in (DefectTriage.Decision.APPROVE, DefectTriage.Decision.EDIT):
            operation_id = triage.final.get("operation_id")
            if not operation_id:
                # Manual review with nothing to apply: closing without changes is the only safe outcome.
                triage.state = DefectTriage.State.REJECTED
            else:
                _reset_operation(operation_id)
                triage.state = DefectTriage.State.APPLIED
                triage.applied_at = timezone.now()
        else:  # dismiss (and reject that reached the limit is routed back to review as manual, never here)
            triage.state = DefectTriage.State.REJECTED
        triage.save()
    return {}


def notify_node(state: TriageState) -> TriageState:
    """After the decision is final: mark the notification and store the closed case as a precedent."""
    triage = _triage(state)
    if triage.state == DefectTriage.State.APPLIED and not DefectCase.objects.filter(triage=triage).exists():
        try:
            add_case(
                defect_type=triage.final.get("defect_type", state.get("classification", {}).get("defect_type")),
                severity=triage.final.get("severity", state.get("classification", {}).get("severity")),
                description=triage.final.get("description", state.get("classification", {}).get("description")),
                cause=triage.final.get("likely_cause", ""),
                resolution=triage.final.get("recommendation", ""),
                triage=triage,
            )
        except Exception:
            logger.exception("failed to store the closed case as a precedent (triage %s)", triage.id)
    triage.notified_at = timezone.now()
    triage.save(update_fields=["notified_at", "updated_at"])
    return {"notified": True}


def _reset_operation(operation_id: str) -> None:
    """Send the chosen operation back to the queue: first status, no start time, editable again."""
    operation = Operation.objects.select_for_update().get(id=operation_id)  # no select_related: nullable FK + FOR UPDATE
    operation.operation_status = OperationStatus.objects.filter(number=1).first()
    operation.exec_start = None
    operation.is_exec_start_editable = True
    operation.save(update_fields=["operation_status", "exec_start", "is_exec_start_editable"])


def _triage(state: TriageState) -> DefectTriage:
    return DefectTriage.objects.get(id=state["triage_id"])


def _after_classify(state: TriageState) -> Node:
    return Node.REVIEW if state.get("manual") else Node.RETRIEVE


def _after_retrieve(state: TriageState) -> Node:
    return Node.REVIEW if state.get("manual") else Node.PROPOSE


def _after_review(state: TriageState) -> Node:
    action = state["decision"]["action"]
    if action == DefectTriage.Decision.REJECT:
        return Node.PROPOSE
    return Node.APPLY  # approve, edit and dismiss are all finalized in apply


def build_graph(checkpointer):
    """Compile the workflow with an injected checkpointer (InMemorySaver in tests, PostgresSaver in production)."""
    graph = StateGraph(TriageState)
    graph.add_node(Node.LOAD_CONTEXT, load_context)
    graph.add_node(Node.CLASSIFY, classify_node)
    graph.add_node(Node.RETRIEVE, retrieve_node)
    graph.add_node(Node.PROPOSE, propose_node)
    graph.add_node(Node.REVIEW, review_node)
    graph.add_node(Node.APPLY, apply_node)
    graph.add_node(Node.NOTIFY, notify_node)

    graph.add_edge(START, Node.LOAD_CONTEXT)
    graph.add_edge(Node.LOAD_CONTEXT, Node.CLASSIFY)
    graph.add_conditional_edges(Node.CLASSIFY, _after_classify,
                                {Node.RETRIEVE: Node.RETRIEVE, Node.REVIEW: Node.REVIEW})
    graph.add_conditional_edges(Node.RETRIEVE, _after_retrieve,
                                {Node.PROPOSE: Node.PROPOSE, Node.REVIEW: Node.REVIEW})
    graph.add_edge(Node.PROPOSE, Node.REVIEW)  # propose always ends in review, with or without a proposal
    graph.add_conditional_edges(Node.REVIEW, _after_review, {Node.PROPOSE: Node.PROPOSE, Node.APPLY: Node.APPLY})
    graph.add_edge(Node.APPLY, Node.NOTIFY)
    graph.add_edge(Node.NOTIFY, END)
    return graph.compile(checkpointer=checkpointer)
