from rest_framework import permissions

from datentool_backend.user.models import PlanningProcess


class CanEditScenarioPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ['POST']:
        # if request.method not in permissions.SAFE_METHODS:
            if request.user.is_superuser:
                return True
            planning_process = PlanningProcess.objects.get(
                id=request.data.get('planning_process'))
            owner_is_user = request.user.profile == planning_process.owner
            user_in_users = request.user.profile in planning_process.users.all()
            allow_shared_change = planning_process.allow_shared_change
            return owner_is_user or (allow_shared_change and user_in_users)
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            owner_is_user = request.user.profile == obj.planning_process.owner
            user_in_users = request.user.profile in obj.planning_process.users.all()
            allow_shared_change = obj.planning_process.allow_shared_change
            return owner_is_user or (allow_shared_change and user_in_users)



