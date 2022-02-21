from rest_framework import permissions
from django.contrib.auth.models import User


class ReadOnlyPermission(permissions.BasePermission):
    """Only user with admin_access or can_edit_basedata have read access.
    Write access is forbidden
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS and (
              request.user.is_superuser or
               request.user.profile.admin_access or
               request.user.profile.can_edit_basedata):
            return True
        return False


class HasAdminAccessOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.method in permissions.SAFE_METHODS or
                request.user.is_superuser or
            request.user.profile.admin_access)


class HasAdminAccessOrReadOnlyAny(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS or
                request.user.is_authenticated and (
                    request.user.is_superuser or
                    request.user.profile.admin_access
                ))


class CanEditBasedata(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                request.user.profile.can_edit_basedata)


class HasAdminAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.profile.admin_access)


class IsOwner(permissions.BasePermission):
    ''' object can only be requested in any way if it is owned by the user '''
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            return obj.id == request.user.id
        return request.user.id == obj.user.id