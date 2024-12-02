from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django import forms
from rest_framework.exceptions import ValidationError

from .models import *


class UserCreationForm(forms.ModelForm):
    """
    Form for creating new users
    """

    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_verified = True
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """
    A form for updating users.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
            "first_name",
            "last_name",
            "is_verified",
        )


class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    ordering = ("email",)

    list_display = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Персональные данные", {"fields": ("first_name", "last_name")}),
        ("Роль", {"fields": ("groups",)}),
        ("Прикрепить заказчиков", {"fields": ("customers",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        ("Персональные данные", {"fields": ("first_name", "last_name")}),
        ("Роль", {"fields": ("groups",)}),
        ("Прикрепить заказчиков", {"fields": ("customers",)}),
    )


admin.site.register(User, UserAdmin)

admin.site.register(Customer)


class DentalLabDataAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "bank_name",
        "bank_id_code",
        "current_account",
        "correspondent_account",
        "tax_payer_id",
        "reason_code_for_reg",
    ]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return not DentalLabData.objects.exists()


admin.site.register(DentalLabData, DentalLabDataAdmin)
