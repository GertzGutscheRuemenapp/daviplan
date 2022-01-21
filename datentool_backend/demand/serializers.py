from rest_framework import serializers

from .models import (AgeGroup, Gender, DemandRateSet, DemandRate)


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = ('id', 'name')


class AgeGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgeGroup
        fields = ('id', 'from_age', 'to_age')


class DemandRateSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandRateSet
        fields = ('id', 'name', 'is_default', 'service')


class DemandRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandRate
        fields = ('id', 'year', 'age_group', 'demand_rate_set', 'value')

