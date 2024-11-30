from django.contrib.admin import ModelAdmin


class BaseModelAdmin(ModelAdmin):
    exclude = ("is_active",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_active=True)

    def delete_model(self, request, obj):
        obj.is_active = False
        obj.save()
