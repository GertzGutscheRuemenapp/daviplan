from rest_framework import viewsets

from django.contrib.auth.models import User
from django.contrib.auth.mixins import UserPassesTestMixin
from .serializers import UserSerializer, ProjectSerializer, ScenarioSerializer
from .models import Project, Scenario

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')

        if pk == "current":
            return self.request.user

        return super().get_object()


class ProjectViewSet(UserPassesTestMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def test_func(self):
        if self.request.method in ('GET'):
            return True
        else:
            return self.request.user.profile.can_create_project

    #def test_func(self):
        #if self.request.method in ('GET'):
            #return True
        #else:
            #return self.request.user.profile.admin_access


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
