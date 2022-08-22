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

    def get_result_type(self, obj) -> str:
        if obj.result_serializer:
            return obj.result_serializer.name.lower()
        return 'none'

    def get_parameters(self, obj) -> List[str]:
        if not obj.params:
            return []
        return [p.serialize() for p in obj.params]


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
