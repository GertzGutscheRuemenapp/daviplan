from rest_framework import viewsets

from .models import Infrastructure, FieldType
from .serializers import InfrastructureSerializer, FieldTypeSerializer


class InfrastructureViewSet(viewsets.ModelViewSet):
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer


class FieldTypeViewSet(viewsets.ModelViewSet):
    queryset = FieldType.objects.all() # prefetch_related('classification_set',
                                         #         to_attr='classifications')
    serializer_class = FieldTypeSerializer
