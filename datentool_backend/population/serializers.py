from rest_framework import serializers


from .models import (Raster, PopulationRaster,
                     Prognosis, Population, PopulationEntry,
                     PopStatistic, PopStatEntry,
                     RasterCellPopulationAgeGender,
                     )


class RasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Raster
        fields = ('id', 'name')


class PopulationRasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationRaster
        fields = ('id', 'name', 'raster', 'year', 'default')


class PrognosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prognosis
        fields = ('id', 'name', 'years', 'is_default')


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
    class Meta:
        model = PopStatistic
        fields = ('id', 'year')


class PopStatEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PopStatEntry
        fields = ('id', 'popstatistic', 'area', 'immigration', 'emigration',
                  'births', 'deaths')


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()
