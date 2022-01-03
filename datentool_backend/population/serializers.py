from rest_framework import serializers
#from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (Raster, PopulationRaster, Gender, AgeGroup, DisaggPopRaster,
                     Prognosis, PrognosisEntry, Population, PopulationEntry,
                     PopStatistic, PopStatEntry)


class RasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Raster
        fields = ('id', 'name')


class PopulationRasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationRaster
        fields = ('id', 'name', 'raster', 'year', 'default')

# ToDo VectorTile
#class RasterCellSerializer(GeoFeatureModelSerializer):
    #class Meta:
        #model = RasterCell
        #geo_field = 'point', 'poly'
        #fields = ('id', 'raster', 'cellcode')


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = ('id', 'name')


class AgeGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgeGroup
        fields = ('id', 'from_age', 'to_age')


class DisaggPopRasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisaggPopRaster
        fields = ('id', 'popraster', 'genders')


class PrognosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prognosis
        fields = ('id', 'name', 'years', 'raster', 'is_default')


class PrognosisEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrognosisEntry
        fields = ('id', 'prognosis', 'year', 'area', 'agegroup',
                  'gender', 'value')


class PopulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Population
        fields = ('id', 'area_level', 'year', 'genders', 'raster')


class PopulationEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationEntry
        fields = ('id', 'population', 'area', 'gender', 'age', 'value')


class PopStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopStatistic
        fields = ('id', 'year')


class PopStatEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PopStatEntry
        fields = ('id', 'popstatistic', 'area', 'immigration', 'emigration',
                  'births', 'deaths')