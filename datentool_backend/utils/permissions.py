from rest_framework import permissions
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.exceptions import PermissionDenied


class BasePermission(permissions.BasePermission):
    def check_demo_mode(self, request):
        '''restrict demo account to read only'''
        if (getattr(settings, 'DEMO_MODE') and
            request.method not in permissions.SAFE_METHODS and
            (request.user.is_anonymous or request.user.profile.is_demo_user)):
            raise PermissionDenied(
                'Der Demo-Modus dient lediglich der Betrachtung. '
                'Sie sind nicht berechtigt mit dem Demo-Konto '
                'Änderungen durchzuführen.')

    def has_permission(self, request, view):
        self.check_demo_mode(request)
        return True

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class ReadOnlyPermission(BasePermission):
    """Only user with admin_access, can_edit_basedata or demo users
    have read access. Write access is forbidden in general
    """
    def has_permission(self, request, view):
        self.check_demo_mode(request)
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS and (
              request.user.is_superuser or
              request.user.profile.admin_access or
              request.user.profile.can_edit_basedata or
              (getattr(settings, 'DEMO_MODE') and
               request.user.profile.is_demo_user)):
            return True
        return False


class HasAdminAccessOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        self.check_demo_mode(request)
        # in demo mode everyone is permitted to read everything
        if (getattr(settings, 'DEMO_MODE') and
            request.method in permissions.SAFE_METHODS):
            return True
        # otherwise log in requiredto read and admin to write
        return request.user.is_authenticated and (
            request.method in permissions.SAFE_METHODS or
                request.user.is_superuser or
            request.user.profile.admin_access)


class HasAdminAccessOrReadOnlyAny(BasePermission):
    def has_permission(self, request, view):
        self.check_demo_mode(request)
        return (request.method in permissions.SAFE_METHODS or
                request.user.is_authenticated and (
                    request.user.is_superuser or
                    request.user.profile.admin_access
                ))


class CanEditBasedata(BasePermission):
    def has_permission(self, request, view):
        self.check_demo_mode(request)
        return (request.user.is_authenticated and
                request.user.profile.can_edit_basedata)


class HasAdminAccess(BasePermission):
    def has_permission(self, request, view):
        self.check_demo_mode(request)
        return (request.user.is_authenticated
                and (request.user.is_superuser or
                     request.user.profile.admin_access))


class IsDemoUser(BasePermission):
    def has_permission(self, request, view):
        return (getattr(settings, 'DEMO_MODE') and
                request.user.is_authenticated and
                request.user.profile.is_demo_user)


class IsOwner(BasePermission):
    ''' object can only be requested in any way if it is owned by the user '''
    def has_permission(self, request, view):
        self.check_demo_mode(request)
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        self.check_demo_mode(request)
        if isinstance(obj, User):
            return obj.id == request.user.id
        return request.user.id == obj.user.id
