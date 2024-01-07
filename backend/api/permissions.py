from rest_framework import permissions
from .models import User


class IsDirector(permissions.BasePermission):
    """
        Permission class for director.
        Director can access everyone root in the application.
    """
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Director')


class IsLabAdmin(permissions.BasePermission):
    """
        Permission class for laboratory administrator.
        Administrator have not access to statistics and cannot perform the operations of technicians.
    """
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Lab admin')


class IsChiefTech(permissions.BasePermission):
    """
        Permission class for chief technician.
        Chief technician have not access to statistics and cannot form an order from ordered products.
    """
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Lead tech')


class IsTech(permissions.BasePermission):
    """
        Permission class for technician.
        Technician can get and complit his operations.
    """
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Tech')
