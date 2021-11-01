from rest_framework import serializers

from .models import Infrastructure


class InfrastructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Infrastructure
        fields =  ('id', 'name', 'description', 
                   'editable_by', 'accessible_by',
                   'layer', 'symbol')

