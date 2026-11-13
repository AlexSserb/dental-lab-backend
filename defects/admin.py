from django.contrib import admin

from .models import DefectCase, DefectTriage


class ReadOnlyAdmin(admin.ModelAdmin):
    """Triages and cases are produced by the workflow; the review actions are added on top of this."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DefectTriage)
class DefectTriageAdmin(ReadOnlyAdmin):
    list_display = ("id", "order", "state", "decision", "revisions", "created_at", "decided_by")
    list_filter = ("state", "decision", "created_at")
    search_fields = ("id", "order__id", "comment")
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in DefectTriage._meta.fields] + ["works"]


@admin.register(DefectCase)
class DefectCaseAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "defect_type", "severity", "operation_type", "source")
    list_filter = ("defect_type", "severity", "source")
    search_fields = ("description", "cause", "resolution")
    exclude = ("embedding",)
    readonly_fields = [f.name for f in DefectCase._meta.fields if f.name != "embedding"]
