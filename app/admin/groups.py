from django.contrib import admin
from django.contrib.auth.models import Group


class GroupAdmin(admin.ModelAdmin):
    exclude = ("permissions",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
