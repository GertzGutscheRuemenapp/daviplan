from typing import List
from rest_framework import serializers


from .models import (Raster, PopulationRaster,
                     Prognosis, Population, PopulationEntry,
                     PopStatistic, PopStatEntry,
                     RasterCellPopulationAgeGender,
                     Year)


use_intersected_data = serializers.BooleanField(
        default=True,
        help_text='''use precalculated rastercells''')
drop_constraints = serializers.BooleanField(
        default=True,
        label='temporarily delete constraints and indices',
        help_text='Set to False in unittests')
area_level = serializers.IntegerField(
        required=False,
        help_text='''if a specific area_level_id is provided,
        take this one instead of the areas of the population''')


class RasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Raster
        fields = ('id', 'name')


class PopulationRasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationRaster
        fields = ('id', 'name', 'raster', 'year', 'default')


class PrognosisSerializer(serializers.ModelSerializer):
    years = serializers.SerializerMethodField()
    class Meta:
        model = Prognosis
        fields = ('id', 'name', 'years', 'is_default')

    def get_years(self, obj) -> List[int]:
        populations = Population.objects.filter(prognosis=obj)
        years = list(populations.values_list('year__year', flat=True).distinct())
        years.sort()
        return years


class RasterCellPopulationAgeGenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = RasterCellPopulationAgeGender
        fields = ('id', 'population', 'cell', 'age_group', 'gender', 'value')


class PopulationDetailSerializer(serializers.ModelSerializer):
    rastercellpopulationagegender_set = RasterCellPopulationAgeGenderSerializer(
        many=True, read_only=True)
    class Meta:
        model = Population
        fields = ('id', 'year', 'genders', 'popraster',
                  'prognosis', 'rastercellpopulationagegender_set')


class PopulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Population
        fields = ('id', 'year', 'genders', 'popraster',
                  'prognosis')


class PopulationEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationEntry
        fields = ('id', 'population', 'area', 'gender', 'age_group', 'value')


class PopStatisticSerializer(serializers.ModelSerializer):
    year = serializers.IntegerField(source='year.year')
    class Meta:
        model = PopStatistic
        fields = ('id', 'year')

    def create(self, validated_data):
        year = validated_data['year']['year']
        instance = PopStatistic.objects.create(year=Year.objects.get(year=year))
        return instance

    def update(self, instance, validated_data):
        year = validated_data['year']['year']
        instance.year = Year.objects.get(year=year)
        instance.save()
        return instance


class PopStatEntrySerializer(serializers.ModelSerializer):
    year = serializers.IntegerField(source='popstatistic.year.year',
                                    read_only=True)
    class Meta:
        model = PopStatEntry
        fields = ('id', 'popstatistic', 'area', 'immigration', 'emigration',
                  'births', 'deaths', 'year')


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()
