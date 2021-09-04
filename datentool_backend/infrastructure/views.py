from rest_framework import viewsets

from .models import Infrastructure
from .serializers import InfrastructureSerializer


class InfrastructureViewSet(viewsets.ModelViewSet):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer
