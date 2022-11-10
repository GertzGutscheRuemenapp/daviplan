from typing import List
import numpy as np

from rest_framework import serializers
from django.db import models

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
    representation = serializers.SerializerMethodField('get_representation')

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

    def get_representation(self, obj) -> str:
        return getattr(obj, 'representation', '')


class RouterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Router
        fields = ('id', 'name', 'osm_file', 'tiff_file', 'gtfs_file',
                  'build_date', 'buffer')



class IndicatorListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        but calculate the median of the values first
        and store them in the child-serializer-attribute `_digits_to_round`
        """
        # Dealing with nested relationships, data can be a Manager,
        # so, first get a queryset from the Manager if needed
        iterable = data.all() if isinstance(data, models.Manager) else data

        if self.child._digits_to_round is None:
            self.child._digits_to_round = self.get_digits(iterable)

        return [
            self.child.to_representation(item) for item in iterable
        ]

    def get_digits(self, iterable) -> int:
        """
        get the number of digits to round the values
        """
        try:
            first_item = iterable[0]
        except IndexError:
            return None

        if isinstance(first_item, dict):
            values = np.array([row['value'] for row in iterable
                                if not row['value'] is None])
        else:
            values = np.array([row.value for row in iterable
                               if not row.value is None])

        if len(values) == 0:
            return None

        median_value = np.nanmedian(values)
        if median_value < 10:
            digits = 2
        elif median_value < 100:
            digits = 1
        else:
            digits = 0
        return digits


class IndicatorDetailSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField('get_value')

    def get_value(self, obj) -> float:
        """
        get the `value`-field as attribute or item
        and round it to the given digits
        """
        try:
            value = obj.value
        except AttributeError:
            value = obj['value']
        if value is None or self._digits_to_round is None:
            return value
        rounded = round(value, self._digits_to_round)
        return rounded

    class Meta:
        list_serializer_class = IndicatorListSerializer


class IndicatorAreaResultSerializer(IndicatorDetailSerializer,
                                    serializers.ModelSerializer):

    label = serializers.CharField()
    area_id = serializers.IntegerField(source='id')
    class Meta(IndicatorDetailSerializer.Meta):
        model = Area
        fields = ('area_id', 'label', 'value')


class IndicatorRasterResultSerializer(IndicatorDetailSerializer,
                                    serializers.ModelSerializer):
    cell_code = serializers.CharField()
    class Meta(IndicatorDetailSerializer.Meta):
        model = RasterCell
        fields = ('cell_code', 'value')


class IndicatorPlaceResultSerializer(IndicatorDetailSerializer,
                                    serializers.ModelSerializer):
    place_id = serializers.IntegerField(source='id')
    class Meta(IndicatorDetailSerializer.Meta):
        model = Place
        fields = ('place_id', 'value')


class IndicatorPopulationSerializer(IndicatorDetailSerializer):
    year = serializers.IntegerField()
    gender = serializers.IntegerField()
    agegroup = serializers.IntegerField()
