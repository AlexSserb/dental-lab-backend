"""
Django admin for the defect workflow: the change pages stay read-only (the workflow owns the data), and the
review decisions are made on a dedicated review page that calls the same decision service as the admin API.
"""
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from accounts.permissions import LAB_ADMIN_GROUP_ID
from defects.models import DefectCase, DefectSeverity, DefectTriage, DefectType
from defects.review import DecisionRejected, decide, similar_cases


class ReadOnlyAdmin(admin.ModelAdmin):
    """Triages and cases are produced by the workflow; the review actions are added on top of this."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DefectTriage)
class DefectTriageAdmin(ReadOnlyAdmin):
    list_display = ("id", "order", "state", "decision", "revisions", "created_at", "review_link")
    list_filter = ("state", "decision", "created_at")
    search_fields = ("id", "order__id", "comment")
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in DefectTriage._meta.fields] + ["works"]

    @admin.display(description="Разбор")
    def review_link(self, triage: DefectTriage):
        url = reverse("admin:defecttriage-review", args=[triage.id])
        return format_html('<a href="{}">Открыть разбор</a>', url)

    def get_urls(self):
        custom = [
            path(
                "triage/<uuid:object_id>/review/",
                self.admin_site.admin_view(self.review_view),
                name="defecttriage-review",
            ),
        ]
        return custom + super().get_urls()

    def review_view(self, request, object_id: str):
        triage = get_object_or_404(DefectTriage, id=object_id)
        if not self._is_lab_admin(request.user):
            return HttpResponseForbidden("Страница разбора доступна только администратору лаборатории.")

        if request.method == "POST":
            if self._handle_decision(request, triage):
                return redirect("admin:defecttriage-review", object_id=triage.id)

        proposal = triage.proposal or {}
        context = {
            **self.admin_site.each_context(request),
            "title": f"Разбор дефекта {triage.id}",
            "triage": triage,
            "works": list(triage.works.select_related("work_type")),
            "proposal": proposal,
            "classification": {
                "description": proposal.get("description", ""),
                "defect_type": proposal.get("defect_type", ""),
                "severity": proposal.get("severity", ""),
            },
            "defect_types": DefectType.choices,
            "severities": DefectSeverity.choices,
            "operations": list(
                triage.works
                .prefetch_related("operations__operation_type")
                .values_list("operations__id", "operations__operation_type__name")
                .order_by("operations__ordinal_number")
            ),
            "similar": similar_cases(triage),
            "awaiting_review": triage.state == DefectTriage.State.AWAITING_REVIEW,
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/defects/triage_review.html", context)

    def _handle_decision(self, request, triage: DefectTriage) -> bool:
        """Turn the submitted form into the same payload the API accepts, and call the shared service."""
        action = request.POST.get("action", "")
        note = request.POST.get("note", "").strip()
        payload: dict = {"action": action, "note": note}

        if action in (DefectTriage.Decision.APPROVE, DefectTriage.Decision.EDIT):
            final = {
                key: request.POST.get(key, "").strip()
                for key in ("operation_id", "description", "defect_type", "severity", "likely_cause", "recommendation")
                if request.POST.get(key, "").strip()
            }
            if action == DefectTriage.Decision.EDIT or final:  # approve with untouched fields sends no final
                payload["final"] = final

        try:
            decide(str(triage.id), request.user, payload)
        except DecisionRejected as rejected:
            if rejected.errors:
                for field, field_errors in rejected.errors.items():
                    messages.error(request, f"{field}: {'; '.join(map(str, field_errors))}")
            else:
                messages.error(request, rejected.detail)
            return False
        messages.success(request, "Решение сохранено — воркер продолжит разбор.")
        return True

    @staticmethod
    def _is_lab_admin(user) -> bool:
        return user.is_superuser or user.groups.filter(id=LAB_ADMIN_GROUP_ID).exists()


@admin.register(DefectCase)
class DefectCaseAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "defect_type", "severity", "operation_type", "source")
    list_filter = ("defect_type", "severity", "source")
    search_fields = ("description", "cause", "resolution")
    exclude = ("embedding",)
    readonly_fields = [f.name for f in DefectCase._meta.fields if f.name != "embedding"]
