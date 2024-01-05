from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from .models import *


class UserAdmin(BaseUserAdmin):
    model = User
    ordering = ('email',)

    list_display = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'old_password', 'new_password', 'new_password2')}),
        ('Personal Information', {'fields': ('first_name', 'last_name')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password', 'password2')}),
        ('Personal Information', {'fields': ('first_name', 'last_name')})
    )


admin.site.register(User, UserAdmin)
admin.site.register(OperationType)
