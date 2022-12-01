from rest_framework import permissions
from datentool_backend.models import Scenario, Service


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


class ScenarioCapacitiesPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
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


class CanEditScenarioPlacePermission(permissions.BasePermission):
    ''' object can only be requested in any way if it is owned by the user '''
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method == 'POST':
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
        if request.method in permissions.SAFE_METHODS:
            return True
        if obj.scenario is None:
            return False
        if request.method in permissions.SAFE_METHODS:
            return obj.scenario.has_read_permission(request.user)
        return obj.scenario.has_write_permission(request.user)


class HasPermissionForScenario(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # service-id comes with the view (detail-view) or as query_params
        service_id = view.kwargs.get('pk', request.query_params.get('service'))

        # if no valid service is provided, deny access
        # check if the infrastructure is permitted for the user
        try:
            service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            return False
        if not service.infrastructure.accessible_by.contains(request.user.profile):
            return False

        # check if the planning process of the scenario is permitted for the user
        scenario_id = request.data.get('scenario', request.query_params.get('scenario'))
        if not scenario_id:
            # the base scenario can be seen by everyone
            # with access to the infrastructure
            return True
        # a specific scenario only if you may see its planning_process
        scenario = Scenario.objects.get(pk=scenario_id)
        return scenario.has_read_permission(request.user)
