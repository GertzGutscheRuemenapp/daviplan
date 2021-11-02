from rest_framework import serializers

from .models import (DemandRateSet, DemandRate)


class DemandRateSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandRateSet
        fields = ('id', 'name', 'is_default', 'age_classification')


class DemandRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandRate
        fields = ('id', 'year', 'age_group', 'demand_rate_set')