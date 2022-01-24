from rest_framework import permissions

from .models import Profile


class CanCreateProcessPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ('GET'):
            return True

        if request.method in ['POST']:
            if request.user.is_superuser:
                return True
            owner = Profile.objects.get(pk=request.data.get('owner'))
            if (request.user.profile.can_create_process
                    and request.user.profile == owner):
                return True
        else:
            return request.user.profile.can_create_process

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return (request.user.profile == obj.owner or
                    request.user.profile in obj.users.all())
        else:
            owner = obj.owner
            return request.user.profile == owner


class CanPatchSymbol(permissions.BasePermission):
    """Permission Class for InfrastructureViewSet, patch of symbol, if user is
    authenticated and can edit basedata """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.profile.admin_access:
            return True
        if request.method in ['PATCH'] + list(permissions.SAFE_METHODS):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if (request.user.is_superuser or request.user.profile.admin_access
                or request.method in permissions.SAFE_METHODS):
            return True
        if (request.user.profile.can_edit_basedata and
                request.method in ('PATCH',) and (
                    len(request.data.keys()) == 0
                    or set(request.data.keys()) <= set(['symbol'])
                )
            ):
            return True
        return False
