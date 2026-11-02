from django.contrib import admin
from django.db.models import Avg, Count, Sum

from .models import LlmCallLog


@admin.register(LlmCallLog)
class LlmCallLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "feature", "model", "user", "tokens", "attempts", "latency", "cost", "success")
    list_filter = ("feature", "model", "success", "created_at")
    search_fields = ("error",)
    readonly_fields = [f.name for f in LlmCallLog._meta.fields]
    change_list_template = "admin/llm/llmcalllog/change_list.html"

    def has_add_permission(self, request):
        return False

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data["cl"].queryset
        except (AttributeError, KeyError):
            return response
        totals = qs.aggregate(calls=Count("id"), cost=Sum("cost"), latency=Avg("latency"), attempts=Avg("attempts"))
        response.context_data["totals"] = totals
        return response
