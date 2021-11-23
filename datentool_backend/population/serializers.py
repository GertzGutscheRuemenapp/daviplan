from rest_framework import serializers
#from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (Year, Raster, PopulationRaster, Gender, AgeClassification,
                     AgeGroup, DisaggPopRaster, Prognosis, PrognosisEntry,
                     Population, PopulationEntry, PopStatistic, PopStatEntry)


class YearSerializer(serializers.ModelSerializer):
    model = Year
    fields = ('id', 'year')


class RasterSerializer(serializers.ModelSerializer):
    model = Raster
    fields = ('id', 'name')


class PopulationRasterSerializer(serializers.ModelSerializer):
    model = PopulationRaster
    fields = ('id', 'name', 'raster', 'year', 'default')

# ToDo VectorTile
#class RasterCellSerializer(GeoFeatureModelSerializer):
    #class Meta:
        #model = RasterCell
        #geo_field = 'point', 'poly'
        #fields = ('id', 'raster', 'cellcode')


class GenderSerializer(serializers.ModelSerializer):
    model = Gender
    fields = ('id', 'gender')


class AgeClassificationSerializer(serializers.ModelSerializer):
    model = AgeClassification
    fields = ('id', 'name')


class AgeGroupSerializer(serializers.ModelSerializer):
    model = AgeGroup
    fields = ('id', 'classification', 'from_age', 'to_age')


class DisaggPopRasterSerializer(serializers.ModelSerializer):
    model = DisaggPopRaster
    fields = ('id', 'popraster', 'genders')


class PrognosisSerializer(serializers.ModelSerializer):
    model = Prognosis
    fields = ('id', 'name', 'years', 'rasters', 'age_classification',
              'is_default')


class PrognosisEntrySerializer(serializers.ModelSerializer):
    model = PrognosisEntry
    fields = ('id', 'prognosis', 'year', 'area', 'agegroup',
              'gender', 'value')


class PopulationSerializer(serializers.ModelSerializer):
    model = Population
    fields = ('id', 'area_level', 'year', 'genders', 'raster')


class PopulationEntrySerializer(serializers.ModelSerializer):
    model = PopulationEntry
    fields = ('id', 'area_level', 'year', 'genders', 'raster')


class PopStatisticSerializer(serializers.ModelSerializer):
    model = PopStatistic
    fields = ('id', 'year')


class PopStatEntrySerializer(serializers.ModelSerializer):
    model = PopStatEntry
    fields = ('id', 'popstatistic', 'area', 'age', 'immigration', 'emigration',
              'births', 'deaths')