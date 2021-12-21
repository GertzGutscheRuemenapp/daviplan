from rest_framework import serializers

from .models import (DemandRateSet, DemandRate, ScenarioDemandRate)


class DemandRateSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandRateSet
        fields = ('id', 'name', 'is_default', 'service')


class DemandRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandRate
        fields = ('id', 'year', 'age_group', 'demand_rate_set', 'value')


class ScenarioDemandRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioDemandRate
        fields = ('id', 'year', 'age_group', 'demand_rate_set', 'value', "scenario")
