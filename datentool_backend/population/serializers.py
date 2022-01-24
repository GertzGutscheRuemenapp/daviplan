from rest_framework import serializers


from .models import (Raster, PopulationRaster, DisaggPopRaster,
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
    #pnt = GeometrySRIDField(srid=3857)
    #poly = GeometrySRIDField(srid=3857)
    #class Meta:
        #model = RasterCell
        #geo_field = 'pnt', 'poly'
        #fields = ('id', 'raster', 'cellcode')


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
        fields = ('id', 'population', 'area', 'gender', 'age_group', 'value')


class PopStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopStatistic
        fields = ('id', 'year')


class PopStatEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PopStatEntry
        fields = ('id', 'popstatistic', 'area', 'immigration', 'emigration',
                  'births', 'deaths')
