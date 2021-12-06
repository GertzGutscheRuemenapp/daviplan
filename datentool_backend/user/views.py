from rest_framework import viewsets

from django.contrib.auth.models import User
from datentool_backend.utils.views import CanCreateProcessPermission
from .serializers import UserSerializer, PlanningProcessSerializer, ScenarioSerializer
from .models import PlanningProcess, Scenario


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == "current":
            return self.request.user

        return super().get_object()


class PlanningProcessViewSet(CanCreateProcessPermission, viewsets.ModelViewSet):
    queryset = PlanningProcess.objects.all()
    serializer_class = PlanningProcessSerializer


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
