"""API schemas of the defect triage review endpoints (admin only)."""
from rest_framework import serializers

from defects.models import DefectTriage, DefectType, DefectSeverity


class TriageListItemSerializer(serializers.Serializer):
    """One row of the pending list."""

    id = serializers.UUIDField(read_only=True)
    order_id = serializers.UUIDField(read_only=True)
    state = serializers.ChoiceField(choices=DefectTriage.State.choices, read_only=True)
    comment = serializers.CharField(read_only=True)
    revisions = serializers.IntegerField(read_only=True)
    decision = serializers.ChoiceField(choices=DefectTriage.Decision.choices, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class TriageWorkSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)


class ProposalSerializer(serializers.Serializer):
    """What the workflow proposes: the classification, the operation to redo, cause and recommendation."""

    description = serializers.CharField(read_only=True)
    defect_type = serializers.ChoiceField(choices=DefectType.values, read_only=True)
    severity = serializers.ChoiceField(choices=DefectSeverity.values, read_only=True)
    operation_id = serializers.UUIDField(read_only=True)
    operation_name = serializers.CharField(read_only=True)
    likely_cause = serializers.CharField(read_only=True)
    recommendation = serializers.CharField(read_only=True)


class SimilarCaseSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    defect_type = serializers.ChoiceField(choices=DefectType.values, read_only=True)
    severity = serializers.ChoiceField(choices=DefectSeverity.values, read_only=True)
    description = serializers.CharField(read_only=True)
    cause = serializers.CharField(read_only=True)
    resolution = serializers.CharField(read_only=True)
    distance = serializers.FloatField(read_only=True)


class TriageDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    order_id = serializers.UUIDField(read_only=True)
    state = serializers.ChoiceField(choices=DefectTriage.State.choices, read_only=True)
    comment = serializers.CharField(read_only=True)
    works = TriageWorkSerializer(many=True, read_only=True)
    proposal = ProposalSerializer(allow_null=True, read_only=True)
    similar_cases = SimilarCaseSerializer(many=True, read_only=True)
    revisions = serializers.IntegerField(read_only=True)
    error = serializers.CharField(read_only=True)
    decision = serializers.ChoiceField(choices=DefectTriage.Decision.choices, read_only=True)
    decision_note = serializers.CharField(read_only=True)
    final = serializers.JSONField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    decided_at = serializers.DateTimeField(allow_null=True, read_only=True)
    applied_at = serializers.DateTimeField(allow_null=True, read_only=True)
    notified_at = serializers.DateTimeField(allow_null=True, read_only=True)
    notify_error = serializers.CharField(read_only=True)


class TriageDecisionSerializer(serializers.Serializer):
    """
    The administrator's answer on the review gate. approve accepts the proposal as is, edit sends corrected
    values in `final`, reject must say in `note` what was wrong, dismiss closes the triage without changes.
    """

    action = serializers.ChoiceField(choices=DefectTriage.Decision.values)
    note = serializers.CharField(max_length=500, allow_blank=True, default="", required=False)
    final = serializers.JSONField(required=False, default=dict)

    def validate(self, attrs):
        action = attrs["action"]
        note = attrs.get("note", "")
        final = attrs.get("final") or {}
        triage = self.context["triage"]
        proposal = triage.proposal or {}

        if action == DefectTriage.Decision.REJECT and not note.strip():
            raise serializers.ValidationError({"note": "Для отклонения нужен комментарий: что именно не так."})
        if action in (DefectTriage.Decision.APPROVE, DefectTriage.Decision.EDIT):
            if action == DefectTriage.Decision.EDIT and not final:
                raise serializers.ValidationError(
                    {"final": "Для правки нужны значения в поле final, иначе это одобрение."}
                )
            operation = self._operation(attrs, final, proposal, triage)
            # final is what apply will execute: the operation the admin confirmed, plus the texts (proposal
            # values unless the admin corrected them).
            attrs["final"] = {
                "operation_id": str(operation.id),
                "operation_name": operation.operation_type.name,
                "description": final.get("description") or proposal.get("description", ""),
                "defect_type": final.get("defect_type") or proposal.get("defect_type", ""),
                "severity": final.get("severity") or proposal.get("severity", ""),
                "likely_cause": final.get("likely_cause") or proposal.get("likely_cause", ""),
                "recommendation": final.get("recommendation") or proposal.get("recommendation", ""),
            }
        else:  # dismiss: nothing to apply
            attrs["final"] = {}
        return attrs

    @staticmethod
    def _operation(attrs, final, proposal, triage):
        from operations.models import Operation

        operation_id = final.get("operation_id") or final.get("operationId") or proposal.get("operation_id")
        if not operation_id:
            raise serializers.ValidationError(
                {"final": "Не выбрана операция: передайте final.operationId или одобрите существующее предложение."}
            )
        # The operation must be one of the reported works: anything else is outside this triage's scope.
        operation = Operation.objects.filter(id=operation_id, work__in=triage.works.all()).first()
        if operation is None:
            raise serializers.ValidationError({"final": "Операция не относится к работам этого разбора."})
        return operation
