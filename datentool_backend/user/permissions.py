from rest_framework import permissions

from .models.process import PlanningProcess, Scenario


class CanUpdateProcessPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (request.user.is_superuser or request.user.profile.admin_access
                or request.user.profile.can_create_process)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return (request.user.profile == obj.owner or
                    request.user.profile in obj.users.all())
        else:
            owner = obj.owner
            return request.user.profile == owner


class CanEditScenarioPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ['POST']:
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
            return obj.has_read_permission(request.user)
        return obj.has_write_permission(request.user)


class CanEditScenarioPlacePermission(permissions.BasePermission):
    ''' object can only be requested in any way if it is owned by the user '''
    def has_permission(self, request, view):
        if request.method not in permissions.SAFE_METHODS:
            scenario_id = request.data.get('scenario')
            if scenario_id is None:
                return False
            try:
                scenario = Scenario.objects.get(id=scenario_id)
                return scenario.has_write_permission(request.user)
            except Scenario.DoesNotExist:
                return False
        return True

    def has_object_permission(self, request, view, obj):
        if obj.scenario is None:
            return False
        if request.method in permissions.SAFE_METHODS:
            return obj.scenario.has_read_permission(request.user)
        return obj.scenario.has_write_permission(request.user)