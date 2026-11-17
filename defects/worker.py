"""
The background worker that drives the defect triage graph.

It polls DefectTriage and does two things:
  - SUBMITTED rows: start the graph for the triage and run it until the review interrupt;
  - DECIDED rows: the administrator has answered (the API stored the decision on the row), resume the
    paused graph with that decision and let it apply and notify.

The claim uses SELECT ... FOR UPDATE SKIP LOCKED, so several workers may run side by side: each row is
taken by exactly one of them, and a row locked by someone else is simply skipped until the next poll.
On any failure the triage is marked FAILED with the error text and the worker keeps polling. Note that a
worker killed mid-graph (SIGKILL, OOM) leaves its row in PROCESSING; such rows need a manual restart of
the run - the checkpointer keeps the state, so re-invoking the thread continues where it stopped.
"""
import logging
import time

from django.conf import settings
from django.db import transaction
from langgraph.types import Command

from defects.graph import build_graph
from defects.models import DefectTriage

logger = logging.getLogger(__name__)

ERROR_TEXT_LIMIT = 2000


def _trace_context(triage: DefectTriage, resume: bool) -> dict:
    """LangSmith run name/tags/metadata for the graph invocation, so traces are searchable in the UI:
    by workflow name, by triage/order id (metadata filters) and by what happened (tags)."""
    return {
        "run_name": "defect-triage",
        "tags": ["defect-triage", "resume" if resume else "initial", triage.state],
        "metadata": {"triage_id": str(triage.id), "order_id": str(triage.order_id), "state": triage.state},
    }


def checkpointer_dsn() -> str:
    """The Postgres connection string for the checkpointer, built from the default database settings."""
    db = settings.DATABASES["default"]
    return (
        f"host={db['HOST'] or 'localhost'} port={db.get('PORT', 5432)} dbname={db['NAME']} "
        f"user={db['USER']} password={db['PASSWORD']}"
    )


class DefectWorker:
    def __init__(self, graph, poll_interval_s: float | None = None):
        self.graph = graph
        self.poll_interval_s = poll_interval_s or settings.DEFECT_WORKER_POLL_S

    def run_forever(self) -> None:
        logger.info("defect worker started (poll every %.1fs)", self.poll_interval_s)
        while True:
            if not self.tick():
                time.sleep(self.poll_interval_s)

    def tick(self) -> bool:
        """One polling pass. Returns True when a triage was picked up and driven."""
        triage = self._claim(DefectTriage.State.SUBMITTED, new_state=DefectTriage.State.PROCESSING)
        if triage is not None:
            self._run(triage, resume=False)
            return True
        triage = self._claim(DefectTriage.State.DECIDED)
        if triage is not None:
            self._run(triage, resume=True)
            return True
        return False

    def _claim(self, state: str, new_state: str | None = None) -> DefectTriage | None:
        """Take one row of `state` that no other worker is holding; optionally move it on to `new_state`."""
        with transaction.atomic():
            row = (
                DefectTriage.objects
                .select_for_update(skip_locked=True)
                .filter(state=state)
                .order_by("created_at")
                .first()
            )
            if row is None:
                return None
            if new_state:
                row.state = new_state
                row.save(update_fields=["state", "updated_at"])
            return row

    def _run(self, triage: DefectTriage, resume: bool) -> None:
        config = {"configurable": {"thread_id": triage.thread_id}, **_trace_context(triage, resume)}
        try:
            if resume:
                self.graph.invoke(Command(resume=self._resume_value(triage)), config=config)
            else:
                self.graph.invoke({"triage_id": str(triage.id)}, config=config)
        except Exception as exc:
            logger.exception("triage %s failed", triage.id)
            # Re-read the row: the graph may have moved it forward before failing. Only open rows are failed;
            # a final state (applied/rejected) is the truth and stays.
            row = DefectTriage.objects.filter(id=triage.id).first()
            if row and row.state in DefectTriage.OPEN_STATES:
                row.state = DefectTriage.State.FAILED
                row.error = f"{type(exc).__name__}: {exc}"[:ERROR_TEXT_LIMIT]
                row.save(update_fields=["error", "state", "updated_at"])

    def _resume_value(self, triage: DefectTriage) -> dict:
        """The decision the administrator made, in the shape the review node expects."""
        return {
            "action": triage.decision,
            "note": triage.decision_note,
            "final": triage.final,
            "decided_by_id": str(triage.decided_by_id) if triage.decided_by_id else None,
        }
