from typing import Dict

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from datentool_backend.utils.geometry_fields import MultiPolygonGeometrySRIDField
from datetime import date as dt_date
from django.urls import reverse
from django.db.models import Max, F, Func

from .models import (MapSymbol, LayerGroup, WMSLayer,
                     Source, AreaLevel, Area,
                     FieldType, FieldTypes, FClass,
                     AreaAttribute, AreaField,
                     )
from datentool_backend.models import PopStatEntry


area_level_id_serializer = serializers.PrimaryKeyRelatedField(
    queryset=AreaLevel.objects.all(),
    help_text='area_level_id',)



class MapSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapSymbol
        fields =  ('symbol', 'fill_color', 'stroke_color')


class LayerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayerGroup
        fields = ('id', 'name', 'order', 'external')


class WMSLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WMSLayer
        fields = ('id', 'name', 'group', 'layer_name', 'order', 'url',
                  'description', 'active')
        optional_fields = ('description', 'active')


class GetCapabilitiesRequestSerializer(serializers.Serializer):
    url = serializers.URLField()
    version = serializers.CharField(required=False, default='1.3.0')


class LayerSerializer(serializers.Serializer):
    name = serializers.CharField()
    title = serializers.CharField()
    abstract = serializers.CharField()
    bbox = serializers.ListField(child=serializers.FloatField(),
                                 min_length=4, max_length=4)


class GetCapabilitiesResponseSerializer(serializers.Serializer):
    version = serializers.CharField()
    url = serializers.URLField()
    cors = serializers.BooleanField()
    layers = LayerSerializer(many=True)


class SourceSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format='%d.%m.%Y',
                                 input_formats=['%d.%m.%Y', 'iso-8601'])
    class Meta:
        model = Source
        fields = ('source_type', 'date', 'url', 'layer')
        extra_kwargs = {'url': {'required': False},
                        'layer': {'required': False},
                        'date': {'required': False}}


class AreaLevelSerializer(serializers.ModelSerializer):
    source = SourceSerializer(allow_null=True, required=False)
    symbol = MapSymbolSerializer(allow_null=True, required=False)
    area_count = serializers.IntegerField(source='area_set.count',
                                          read_only=True)
    tile_url = serializers.SerializerMethodField(read_only=True)
    max_values = serializers.SerializerMethodField(read_only=True)
    area_fields = serializers.SerializerMethodField(read_only=True)
    label_field = serializers.CharField(required=False)
    key_field = serializers.CharField(required=False)

    class Meta:
        model = AreaLevel
        fields = ('id', 'name', 'order', 'source', 'symbol', 'is_active',
                  'is_preset', 'area_count', 'tile_url', 'label_field',
                  'max_values', 'is_statistic_level', 'is_default_pop_level',
                  'area_fields', 'label_field', 'key_field')
        read_only_fields = ('is_preset', 'is_statistic_level')

    def get_max_values(self, obj) -> Dict[str, float]:
        ret = {'population': obj.max_population}
        if obj.is_statistic_level:
            entries = PopStatEntry.objects.all().annotate(
                migration_diff=Func(F('immigration') - F('emigration'), function='ABS'),
                nature_diff=Func(F('births') - F('deaths'), function='ABS'),
            )
            mvs = entries.aggregate(Max('immigration'), Max('emigration'),
                                    Max('births'), Max('deaths'),
                                    Max('nature_diff'), Max('migration_diff'))
            ret['immigration'] = mvs['immigration__max']
            ret['emigration'] = mvs['emigration__max']
            ret['births'] = mvs['births__max']
            ret['deaths'] = mvs['deaths__max']
            ret['nature_diff'] = mvs['nature_diff__max']
            ret['migration_diff'] = mvs['migration_diff__max']
        return ret

    def get_area_fields(self, obj):
        return obj.areafield_set.values_list('name', flat=True)

    def get_tile_url(self, obj) -> str:
        # x,y,z have to be passed to reverse
        url = reverse('layer-tile', kwargs={'pk': obj.id, 'z': 0,
                                            'x': 0, 'y': 0})
        # split off trailing x,y,z
        url = url.split('/0/0/0')[0]
        # incl. host
        url = self.context['request'].build_absolute_uri(url)
        # add generic x,y,z specs
        url += '/{z}/{x}/{y}/'
        return url

    def create(self, validated_data):
        symbol_data = validated_data.pop('symbol', {})
        if not 'symbol' in symbol_data:
            symbol_data['symbol'] = 'line'
        symbol = MapSymbol.objects.create(**symbol_data) \
            if symbol_data else None
        source_data = validated_data.pop('source', {})
        #date = source_data.pop('date', dt_date.today())
        source = Source.objects.create(**source_data)

        instance = AreaLevel.objects.create(
            symbol=symbol, source=source, **validated_data)

        return instance

    def update(self, instance, validated_data):
        #  you are not allowed to change names of presets
        if (instance.is_preset):
            validated_data.pop('name', None)
        # symbol is nullable
        update_symbol = 'symbol' in validated_data
        symbol_data = validated_data.pop('symbol', None)
        # source is nullable
        update_source = 'source' in validated_data
        source_data = validated_data.pop('source', None)

        # ToDo: set label field, key field
        #label_field = validated_data.pop('label_field', None)
        #if label_field:
            ## ToDo: does setting to None work this way?
            #instance.areafield_set.update(is_label=None)
            ## ToDo: field type
            #field = AreaField.objects.get_or_create(
                #area_level=instance, name=label_field)
            #field.is_label = True
            #field.save()
        #key_field = validated_data.pop('label_field', None)
        #if key_field:
            #instance.areafield_set.update(is_label=None)
            #field = AreaField.objects.get_or_create(
                #area_level=instance, name=label_field)
            #field.is_key = True
            #field.save()

        instance = super().update(instance, validated_data)
        if update_symbol:
            symbol = instance.symbol
            if symbol_data:
                if not symbol:
                    if not 'symbol' in symbol_data:
                        symbol_data['symbol'] = 'line'
                    symbol = MapSymbol.objects.create(**symbol_data)
                    instance.symbol = symbol
                else:
                    for k, v in symbol_data.items():
                        setattr(symbol, k, v)
                    symbol.save()
            # symbol passed but is None -> intention to set it to null
            else:
                symbol.delete()
                instance.symbol = None

        if update_source:
            source = instance.source
            if source_data:
                date = source_data.pop('date', dt_date.today())
                if not source:
                    source = Source.objects.create(date=date, **source_data)
                    instance.source = source
                else:
                    for k, v in source_data.items():
                        setattr(source,  k, v)
                    source.save()
            # source passed but is None -> intention to set it to null
            else:
                source.delete()
                instance.source = None

        instance.save()
        return instance


class FClassSerializer(serializers.ModelSerializer):
    ftype_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        source='ftype',
        queryset=FieldType.objects.all())

    class Meta:
        model = FClass
        read_only_fields = ('id', 'ftype', )
        write_only_fields = ('ftype_id', )
        fields = ('id', 'order', 'value',
                  'ftype', 'ftype_id')


class FieldTypeSerializer(serializers.ModelSerializer):

    classification = FClassSerializer(required=False, many=True,
                                      source='fclass_set')

    class Meta:
        model = FieldType
        fields = ('id', 'name', 'ftype', 'classification')

    def create(self, validated_data):
        classification_data = validated_data.pop('fclass_set', {})
        instance = super().create(validated_data)
        instance.save()
        if classification_data and instance.ftype == FieldTypes.CLASSIFICATION:
            for classification in classification_data:
                fclass = FClass(order=classification['order'],
                                ftype=instance,
                                value=classification['value'])
                fclass.save()
        return instance

    def update(self, instance, validated_data):
        classification_data = validated_data.pop('fclass_set', {})
        instance = super().update(instance, validated_data)
        if classification_data and instance.ftype == FieldTypes.CLASSIFICATION:
            classification_list = []
            for classification in classification_data:
                fclass = FClass(order=classification['order'],
                                ftype=instance,
                                value=classification['value'])
                fclass.save()
                classification_list.append(fclass)
            classification_data_ids = [f.id for f in classification_list]
            for fclass in instance.fclass_set.all():
                if fclass.id not in classification_data_ids:
                    fclass.delete(keep_parents=True)
        return instance


class AreaAttributeField(serializers.JSONField):

    def to_representation(self, value):
        data = {aa.field.name: aa.value for aa in value.iterator()}
        return data


class AreaSerializer(GeoFeatureModelSerializer):
    geom = MultiPolygonGeometrySRIDField(srid=3857)
    attributes = AreaAttributeField(source='areaattribute_set')
    label = serializers.SerializerMethodField()
    key = serializers.SerializerMethodField()

    class Meta:
        model = Area
        geo_field = 'geom'
        fields = ('id', 'area_level', 'attributes', 'label', 'key')

    def get_label(self, obj: Area) -> str:
        return obj.label

    def get_key(self, obj: Area) -> str:
        return obj.key

    def create(self, validated_data):
        """
        Create and return a new `Area` instance, given the validated data.
        """
        attributes = validated_data.pop('areaattribute_set')
        area = super().create(validated_data)

        for field_name, value in attributes.items():
            field = AreaField.objects.get(area_level=area.area_level,
                                          name=field_name)
            AreaAttribute.objects.create(area=area,
                                         field=field,
                                         value=value)
        return area

    def update(self, instance, validated_data):
        """
        Update an Area instance, given the validated data.
        """
        attributes = validated_data.pop('areaattribute_set')
        area = super().update(instance, validated_data)

        existing_area_attributes = AreaAttribute.objects.filter(area=area)
        existing_area_attributes.delete()

        for field_name, value in attributes.items():
            field = AreaField.objects.get(area_level=area.area_level,
                                          name=field_name)
            AreaAttribute.objects.create(area=area,
                                         field=field,
                                         value=value)
        return instance
