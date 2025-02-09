from django.contrib import admin
from django.contrib.sites.models import Site


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
