from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site


class BaseModelAdmin(ModelAdmin):
    exclude = ("is_active",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_active=True)

    def delete_model(self, request, obj):
        obj.is_active = False
        obj.save()


class BaseStatusAdmin(BaseModelAdmin):
    ordering = ("number",)
    exclude = ("number", "is_active")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class GroupAdmin(admin.ModelAdmin):
    exclude = ("permissions",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)


class SitesAdmin(admin.ModelAdmin):
    def has_view_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(Site)
admin.site.register(Site, SitesAdmin)
