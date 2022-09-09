from typing import List
from rest_framework import serializers

from datentool_backend.indicators.models import Router
from datentool_backend.area.models import Area
from datentool_backend.population.models import RasterCell
from datentool_backend.infrastructure.models.places import Place


class IndicatorSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    title = serializers.CharField()
    result_type = serializers.SerializerMethodField('get_result_type')
    additional_parameters = serializers.SerializerMethodField('get_parameters')
    unit = serializers.SerializerMethodField('get_unit')
    decimals = serializers.SerializerMethodField('get_decimals')
    interpolated = serializers.SerializerMethodField('get_interpolated')
    representation = serializers.SerializerMethodField('get_representation')
    classification = serializers.SerializerMethodField('get_classification')
    colorscheme = serializers.SerializerMethodField('get_colorscheme')

    def get_result_type(self, obj) -> str:
        if obj.result_serializer:
            return obj.result_serializer.name.lower()
        return 'none'

    def get_parameters(self, obj) -> List[str]:
        if not obj.params:
            return []
        return [p.serialize() for p in obj.params]

    def get_unit(self, obj) -> str:
        return getattr(obj, 'unit', '')

    def get_decimals(self, obj) -> int:
        return getattr(obj, 'decimals', '')

    def get_interpolated(self, obj) -> bool:
        return getattr(obj, 'interpolated', '')

    def get_representation(self, obj) -> str:
        return getattr(obj, 'representation', '')

    def get_classification(self, obj) -> List[int]:
        return getattr(obj, 'classification', [])

    def get_colorscheme(self, obj) -> List[str]:
        return getattr(obj, 'colorscheme', [])


class RouterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Router
        fields = ('id', 'name', 'osm_file', 'tiff_file', 'gtfs_file',
                  'build_date', 'buffer')


class IndicatorAreaResultSerializer(serializers.ModelSerializer):
    label = serializers.CharField()
    value = serializers.FloatField()
    area_id = serializers.IntegerField(source='id')
    class Meta:
        model = Area
        fields = ('area_id', 'label', 'value')


class IndicatorRasterResultSerializer(serializers.ModelSerializer):
    cell_code = serializers.CharField()
    value = serializers.FloatField()
    class Meta:
        model = RasterCell
        fields = ('cell_code', 'value')


class IndicatorPlaceResultSerializer(serializers.ModelSerializer):
    place_id = serializers.IntegerField(source='id')
    value = serializers.FloatField()
    class Meta:
        model = Place
        fields = ('place_id', 'value')


class IndicatorPopulationSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    gender = serializers.IntegerField()
    agegroup = serializers.IntegerField()
    value = serializers.FloatField()
