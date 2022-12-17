from typing import Dict
from rest_framework.exceptions import NotAcceptable
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from datetime import date as dt_date
from django.urls import reverse
from django.db.models import Max, F, Func
from django.db.models.functions import Cast, Coalesce

from datentool_backend.area.models import (MapSymbol,
                     Source, AreaLevel, TextField,
                     FieldType, FieldTypes, FClass,
                     AreaAttribute, AreaField,
                     )
from datentool_backend.models import PopStatEntry

from .layers import SourceSerializer, MapSymbolSerializer


area_level_id_serializer = serializers.PrimaryKeyRelatedField(
    queryset=AreaLevel.objects.all(),
    help_text='area_level_id',)


class AreaLevelSerializer(serializers.ModelSerializer):
    source = SourceSerializer(allow_null=True, required=False)
    symbol = MapSymbolSerializer(allow_null=True, required=False)
    area_count = serializers.IntegerField(source='area_set.count',
                                          read_only=True)
    tile_url = serializers.SerializerMethodField(read_only=True)
    max_values = serializers.SerializerMethodField(read_only=True)
    area_fields = serializers.SerializerMethodField(read_only=True)
    label_field = serializers.CharField(allow_null=True, required=False)
    key_field = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = AreaLevel
        fields = ('id', 'name', 'order', 'source', 'symbol', 'is_active',
                  'is_preset', 'area_count', 'tile_url', 'label_field',
                  'max_values', 'is_statistic_level', 'is_default_pop_level',
                  'is_pop_level', 'area_fields', 'key_field')
        read_only_fields = ('is_preset', 'is_statistic_level',
                            'is_default_pop_level')

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
        url = reverse('areas-tile', kwargs={'pk': obj.id, 'z': 0,
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

        key_field = validated_data.pop('key_field', None)
        # ToDo: validate uniqueness of column, return HTTPError otherwise
        if key_field:
            field, created = AreaField.objects.get_or_create(
                area_level=instance, name=key_field)
            attributes = (
                AreaAttribute.objects.filter(field=field)
                .select_related('field__field_type', 'class_value')
                .annotate(_value=Coalesce(
                    F('str_value'), Coalesce(Cast(F('num_value'), TextField()),
                                             F('class_value__value')))))
            unique = (attributes.values('_value').distinct().count() ==
                      attributes.count())
            if not unique:
                raise ValidationError(f'Die Werte des Feldes "{key_field}" '
                                      'sind nicht eindeutig!')
            instance.areafield_set.update(is_key=None)
            field.is_key = True
            field.save()

        #  you are not allowed to change names of presets
        if (instance.is_preset):
            validated_data.pop('name', None)
        # symbol is nullable
        update_symbol = 'symbol' in validated_data
        symbol_data = validated_data.pop('symbol', None)
        # source is nullable
        update_source = 'source' in validated_data
        source_data = validated_data.pop('source', None)

        label_field = validated_data.pop('label_field', None)
        if label_field:
            instance.areafield_set.update(is_label=None)
            # ToDo: field type
            field, created = AreaField.objects.get_or_create(
                area_level=instance, name=label_field)
            field.is_label = True
            field.save()

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
            elif symbol:
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
    ftype_id = serializers.IntegerField(
        write_only=True,
        required=False)

    class Meta:
        model = FClass
        read_only_fields = ('id', 'ftype', )
        fields = ('id', 'order', 'value',
                  'ftype', 'ftype_id')


class FieldTypeSerializer(serializers.ModelSerializer):

    classification = FClassSerializer(required=False, many=True,
                                      source='fclass_set')

    class Meta:
        model = FieldType
        fields = ('id', 'name', 'is_preset', 'ftype', 'classification')
        read_only_fields = ('is_preset',)

    def create(self, validated_data):
        classification_data = validated_data.pop('fclass_set', None)
        instance = super().create(validated_data)
        instance.save()
        if classification_data is not None and instance.ftype == FieldTypes.CLASSIFICATION:
            self._update_classification(instance, classification_data)
        return instance

    def update(self, instance, validated_data):
        classification_data = validated_data.pop('fclass_set', None)
        instance = super().update(instance, validated_data)
        if classification_data is not None and instance.ftype == FieldTypes.CLASSIFICATION:
            self._update_classification(instance, classification_data)
        return instance

    def _update_classification(self, instance, data):
        """update the classifications for the fieldtype"""
        # assert that the names are unique
        names = [f['value'] for f in data]
        if (len(set(names)) != len(names)):
            raise NotAcceptable('Die Werte der Klassen müssen einzigartig sein!')

        # delete unused classifications
        new_values = [d['value'] for d in data]
        fields_fclasses = FClass.objects.filter(ftype=instance)
        to_delete = fields_fclasses.exclude(value__in=new_values)
        to_delete.delete()

        # update order of existing values and create new values in one transaction
        # with bulk_update/create - to assure the unique constraint on order is met
        fclasses_to_update = []
        fclasses_to_create = []
        for classification in data:
            order = classification.get('order', 0)
            try:
                fclass = fields_fclasses.get(value=classification['value'])
                fclass.order = order
                fclasses_to_update.append(fclass)
            except FClass.DoesNotExist:
                fclass = FClass(
                    ftype=instance, value=classification['value'], order=order)
                fclasses_to_create.append(fclass)
        FClass.objects.bulk_update(fclasses_to_update, fields=['order'])
        # new objects are appended at the end if order is conflicting
        if fclasses_to_create:
            max_order = fields_fclasses.aggregate(Max('order'))['order__max']
        for fclass in fclasses_to_create:
            if fields_fclasses.filter(order__contains=fclass.order):
                max_order += 1
                fclass.order = max_order
        FClass.objects.bulk_create(fclasses_to_create)


class AreaFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaField
        fields = ('id', 'name', 'area_level', 'is_label', 'is_key', 'field_type',)
