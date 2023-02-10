from rest_framework import permissions


class CanPatchSymbol(permissions.BasePermission):
    """Permission Class for InfrastructureViewSet, patch of symbol, if user is
    authenticated and can edit basedata """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.profile.admin_access:
            return True
        # patch infrastructure is checked in object-permission
        if request.method in ['PATCH'] + list(permissions.SAFE_METHODS):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if (request.user.is_superuser or request.user.profile.admin_access
            or request.method in permissions.SAFE_METHODS):
            return True
        # base data editors are only allowed to patch the symbol and the fields
        if (request.user.profile.can_edit_basedata and
                request.method in ('PATCH',) and (
                    len(request.data.keys()) == 0
                    or set(request.data.keys()) <= set(['symbol', 'place_fields'])
                )
            ):
            return True
        return False
