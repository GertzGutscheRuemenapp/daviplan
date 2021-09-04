from rest_framework import serializers

from .models import Infrastructure


class InfrastructureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Infrastructure
        fields =  ('name', 'description', 'editable_by',
                   'accessible_by', 'layer', 'symbol')

