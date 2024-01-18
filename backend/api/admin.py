from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from .models import *


class UserCreationForm(forms.ModelForm):
    """
    Form for creating new users
    """

    password1 = forms.CharField(
        label='Password', widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label='Password confirmation', widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

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
        fields = ('email', 'password', 'is_active', 'is_staff', 'is_superuser', 'first_name', 'last_name')


class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    ordering = ('email',)

    list_display = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Information', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('groups',)}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')}),
        ('Personal Information', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('groups',)}),
    )


admin.site.register(User, UserAdmin)

admin.site.register(OperationType)

class OperationTypeProductTypeInline(admin.TabularInline):
    verbose_name = 'операция для выполнения изделия'
    verbose_name_plural = 'операции для выполнения изделия'
    model = OperationTypeProductType
    extra = 1

class ProductTypeAdmin(admin.ModelAdmin):
    inlines = (
        OperationTypeProductTypeInline,
    )
    fieldsets = (
        (None, { 'fields': ('name', ), }),
    )


admin.site.register(ProductType, ProductTypeAdmin)

admin.site.register(OperationStatus)
admin.site.register(ProductStatus)
admin.site.register(OrderStatus)
admin.site.register(Order)
admin.site.register(Product)
admin.site.register(Tooth)
admin.site.register(Operation)
