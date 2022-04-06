from django.db.models import Min
from rest_framework import serializers

from datentool_backend.infrastructure.models.infrastructures import Service
from datentool_backend.infrastructure.models.places import Capacity


class ServiceSerializer(serializers.ModelSerializer):
    max_capacity = serializers.IntegerField(read_only=True)
    min_capacity = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'infrastructure', 'editable_by',
                  'capacity_singular_unit', 'capacity_plural_unit',
                  'has_capacity', 'demand_singular_unit', 'demand_plural_unit',
                  'quota_type', 'demand_name', 'demand_description',
                  'min_capacity', 'max_capacity',
                  'facility_singular_unit', 'facility_article',
                  'facility_plural_unit', 'direction_way_relationship')

    def get_min_capacity(self, obj) -> float:
        mc = Capacity.objects.filter(capacity__gt=0).aggregate(
            min_cap=Min('capacity'))
        return mc['min_cap']