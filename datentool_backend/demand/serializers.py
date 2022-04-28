from rest_framework import serializers

from .models import (AgeGroup, Gender, DemandRateSet, DemandRate, Year)


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = ('id', 'name')


class AgeGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgeGroup
        fields = ('id', 'from_age', 'to_age')


class DemandRateSerializer(serializers.ModelSerializer):
    filter_fields = ['demand_rate_set']
    year = serializers.IntegerField(source='year.year')
    class Meta:
        model = DemandRate
        fields = ('year', 'age_group', 'gender', 'value')


class DemandRateSetSerializer(serializers.ModelSerializer):
    demand_rates = DemandRateSerializer(many=True, required=False,
                                        source='demandrate_set')
    class Meta:
        model = DemandRateSet
        fields = ('id', 'name', 'is_default', 'service', 'description',
                  'demand_rates')
        extra_kwargs = {'description': {'required':  False}}

    @classmethod
    def apply_demandrates(cls, instance, demand_rate_data):
        new_demand_rates = []
        for dr in demand_rate_data:
            value = dr.pop('value', 0)
            dr['year'] = Year.objects.get(year=dr.pop('year')['year'])
            dr['demand_rate_set'] = instance
            demand_rate, created = DemandRate.objects.get_or_create(**dr)
            new_demand_rates.append(demand_rate.id)
            demand_rate.value = value
            demand_rate.save()
        # delete all previously existing and not updated demand rates
        DemandRate.objects.filter(demand_rate_set=instance).exclude(
            id__in=new_demand_rates).delete()

    def create(self, validated_data):
        demand_rate_data = validated_data.pop('demandrate_set', None)
        instance = super().create(validated_data)
        if (demand_rate_data):
            self.apply_demandrates(instance, demand_rate_data)
        return instance

    def update(self, instance, validated_data):
        demand_rate_data = validated_data.pop('demandrate_set', None)
        instance = super().update(instance, validated_data)
        if (demand_rate_data):
            self.apply_demandrates(instance, demand_rate_data)
        return instance
