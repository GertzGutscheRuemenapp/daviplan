from rest_framework import viewsets

from django.contrib.auth.models import User
# from datentool_backend.utils.views import BaseProfilePermissionMixin
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


class PlanningProcessViewSet(viewsets.ModelViewSet):
    queryset = PlanningProcess.objects.all()
    serializer_class = PlanningProcessSerializer

#  Rechte anhand des Profils vergeben
    #def get_test_func(self):
        #return self.check_can_create_process


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
