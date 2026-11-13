from rest_framework import permissions
from django.contrib.auth import get_user_model


User = get_user_model()

LAB_ADMIN_GROUP_ID = 1


class IsLabAdmin(permissions.BasePermission):
    """
        Permission class for laboratory administrator.
    """
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(id=LAB_ADMIN_GROUP_ID)


class IsTech(permissions.BasePermission):
    """
        Permission class for technician.
        Technician can get and complete his operations.
    """
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(id__in=(2, 3, 4, 5))
