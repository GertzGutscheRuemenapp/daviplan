from typing import List
from rest_framework import serializers

from datentool_backend.population.models import (Raster,
                                                 PopulationRaster,
                                                 RasterCell,
                                                 Prognosis,
                                                 Population,
                                                 PopulationEntry,
                                                 PopStatistic,
                                                 PopStatEntry,
                                                 RasterCellPopulationAgeGender)
from datentool_backend.site.models import Year


class RasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Raster
        fields = ('id', 'name')


class RasterCellSerializer(serializers.ModelSerializer):
    geom = serializers.JSONField()
    #poly = MultiPolygonGeometrySRIDField(srid=3857)
    population = serializers.FloatField()
    class Meta:
        model = RasterCell
        #geo_field = 'poly'
        fields = ('id', 'cellcode', 'population', 'geom')


class PopulationRasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationRaster
        fields = ('id', 'name', 'raster', 'default', 'filename', 'srid')


class PrognosisSerializer(serializers.ModelSerializer):
    years = serializers.SerializerMethodField()
    class Meta:
        model = Prognosis
        fields = ('id', 'name', 'years', 'is_default', 'description')
        extra_kwargs = {'description': {'required': False}}

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
