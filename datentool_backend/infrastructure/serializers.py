import json
from rest_framework.validators import ValidationError
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework.fields import JSONField, empty
from django.db.models import Window
from django.db.models.functions import Coalesce, Lead

from .models import (Infrastructure, FieldType, FClass, FieldTypes, Service,
                     Place, Capacity, PlaceField, InfrastructureAccess)
from datentool_backend.utils.geometry_fields import GeometrySRIDField
from datentool_backend.area.models import LayerGroup, MapSymbol
from datentool_backend.area.serializers import MapSymbolSerializer


class InfrastructureAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureAccess
        fields = ('id', 'infrastructure', 'profile', 'allow_sensitive_data')
        read_only_fields = ('id', 'infrastructure', )


class InfrastructureSerializer(serializers.ModelSerializer):
    symbol = MapSymbolSerializer(allow_null=True, required=False)
    accessible_by = InfrastructureAccessSerializer(
        many=True, source='infrastructureaccess_set', required=False)

    class Meta:
        model = Infrastructure
        fields = ('id', 'name', 'description',
                  'editable_by', 'accessible_by',
                  'order', 'symbol')

    def create(self, validated_data):
        symbol_data = validated_data.pop('symbol', None)
        symbol = MapSymbol.objects.create(**symbol_data) \
            if symbol_data else None

        editable_by = validated_data.pop('editable_by', [])
        accessible_by = validated_data.pop('infrastructureaccess_set', [])
        instance = Infrastructure.objects.create(
            symbol=symbol, **validated_data)
        instance.editable_by.set(editable_by)
        instance.accessible_by.set([a['profile'] for a in accessible_by])
        for profile_access in accessible_by:
            infrastructure_access = InfrastructureAccess.objects.get(
                infrastructure=instance,
                profile=profile_access['profile'])
            infrastructure_access.allow_sensitive_data = profile_access['allow_sensitive_data']
            infrastructure_access.save()

        return instance

    def update(self, instance, validated_data):
        # symbol is nullable
        update_symbol = 'symbol' in validated_data
        symbol_data = validated_data.pop('symbol', None)

        editable_by = validated_data.pop('editable_by', None)
        accessible_by = validated_data.pop('infrastructureaccess_set', None)
        instance = super().update(instance, validated_data)
        if editable_by is not None:
            instance.editable_by.set(editable_by)
        if accessible_by is not None:
            instance.accessible_by.set([a['profile'] for a in accessible_by])
            for profile_access in accessible_by:
                infrastructure_access = InfrastructureAccess.objects.get(
                    infrastructure=instance,
                    profile=profile_access['profile'])
                infrastructure_access.allow_sensitive_data = profile_access['allow_sensitive_data']
                infrastructure_access.save()

        if update_symbol:
            symbol = instance.symbol
            if symbol_data:
                if not symbol:
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

        instance.save()
        return instance


class ServiceSerializer(serializers.ModelSerializer):
    #quota_id = serializers.IntegerField(write_only=True, source='quota')
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'infrastructure', 'editable_by',
                  'capacity_singular_unit', 'capacity_plural_unit',
                  'has_capacity', 'demand_singular_unit', 'demand_plural_unit',
                  'quota_type')


class PlaceAttributeField(JSONField):
    """remove sensitive fields if the user is not allowed to see them"""

    def get_attribute(self, instance):
        place = instance
        value = super().get_attribute(instance)
        value_dict = json.loads(value)
        profile = self.context['request'].user.profile
        infra_access = InfrastructureAccess.objects.get(
            infrastructure=place.infrastructure, profile=profile)
        if not infra_access.allow_sensitive_data:
            fields = PlaceField.objects.filter(infrastructure=place.infrastructure)
            for field in fields:
                if field.sensitive:
                    value_dict.pop(field.attribute, None)
        return json.dumps(value_dict)

    def run_validation(self, data=empty):
        """
        Validate a simple representation and return the internal value.

        The provided data may be `empty` if no representation was included
        in the input.

        May raise `SkipField` if the field should not be included in the
        validated data.
        """
        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data
        # convert to dict
        value = self.to_internal_value(data)
        # run validators that might change the entries in the dict
        self.run_validators(value)
        # convert back to json
        value = json.dumps(value)
        return value

    def to_internal_value(self, data):
        """convert to dict if data is gives as json"""
        if isinstance(data, str):
            data = json.loads(data)
        data = super().to_internal_value(data)
        return data


class PlaceAttributeValidator:
    """validate the place attribute"""
    requires_context = True

    def __call__(self, value, field):
        """"""
        new_attributes = value
        place = field.parent.instance
        if place:
            infrastructure = place.infrastructure
        else:
            properties = field.parent.initial_data.get('properties')
            if not properties:
                infrastructure_id = field.parent.initial_data.get('infrastructure')
            else:
                infrastructure_id = properties.get('infrastructure')
            if infrastructure_id is None:
                raise ValidationError('No infrastructure_id provided')
            infrastructure = Infrastructure.objects.get(pk=infrastructure_id)

        infr_name = infrastructure.name

        for field_name, field_value in new_attributes.items():
            # check if the fields exist as a PlaceField
            try:
                place_field = PlaceField.objects.get(
                    attribute=field_name,
                    infrastructure=infrastructure)
            except PlaceField.DoesNotExist:
                msg = f'Field {field_name} is no PlaceField for Infrastructure {infr_name}'
                raise ValidationError(msg)
            # check if the value is of correct type
            field_type = place_field.field_type
            if not field_type.validate_datatype(field_value):
                ft = FieldTypes(field_type.field_type)
                msg = f'''Field '{field_name}' for Infrastructure '{infr_name}'
                should be of {field_type}({ft.label})'''
                if field_type.field_type == FieldTypes.CLASSIFICATION:
                    fclasses = list(
                        FClass.objects.filter(classification=field_type)
                        .values_list('value', flat=True))
                    msg += f'.The value {field_value!r} is not in the valid classes {fclasses}.'
                else:
                    msg += f''', but the value is {field_value!r}.'''
                raise ValidationError(msg)

        if place:
            # update the new attributes with existing attributes,
            # if the field is not specified
            attributes = json.loads(place.attributes)
            for k, v in attributes.items():
                if k not in new_attributes:
                    new_attributes[k] = v


class PlaceUpdateAttributeSerializer(serializers.ModelSerializer):
    attributes = PlaceAttributeField(validators=[PlaceAttributeValidator()])

    class Meta:
        model = Place
        fields = ('name', 'attributes')


class CapacityListSerializer(serializers.ListSerializer):

    def to_representation(self, instance):
        request = self.context.get('request')
        if request:
            #  filter the capacity returned for the specific service
            service_id = request.query_params.get('service')
            if service_id:
                instance = instance.filter(service_id=service_id)

            #  filter the queryset by year
            year = request.query_params.get('year', 0)
            instance_year = instance\
                .filter(from_year__lte=year)\
                .filter(to_year__gte=year)

            # filter the queryset by scenario
            scenario = request.query_params.get('scenario')
            instance = instance_year\
                .filter(scenario=scenario)
            if not instance:
                instance = instance_year.filter(scenario=None)

        return super().to_representation(instance)


class CapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Capacity
        list_serializer_class = CapacityListSerializer
        fields = ('id', 'place', 'service', 'capacity', 'from_year', 'scenario')


class CapacityAmountSerializer(serializers.FloatField):
    def to_representation(self, item) -> str:
        return super().to_representation(item.capacity)


class PlaceSerializer(GeoFeatureModelSerializer):
    geom = GeometrySRIDField(srid=3857)
    attributes = PlaceAttributeField(validators=[PlaceAttributeValidator()])
    capacity = CapacitySerializer(required=False, many=True,
                                  source='capacity_set')
    capacities = CapacityListSerializer(required=False,
                                        child=CapacityAmountSerializer(),
                                        source='capacity_set')


    class Meta:
        model = Place
        geo_field = 'geom'
        fields = ('id', 'name', 'infrastructure', 'attributes', 'capacity',
                  'capacities', 'scenario')



class FClassSerializer(serializers.ModelSerializer):
    classification_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        source='classification',
        queryset=FieldType.objects.all())

    class Meta:
        model = FClass
        read_only_fields = ('id', 'classification', )
        write_only_fields = ('classification_id', )
        fields = ('id', 'order', 'value',
                  'classification', 'classification_id')


class FieldTypeSerializer(serializers.ModelSerializer):

    classification = FClassSerializer(required=False, many=True,
                                      source='fclass_set')

    class Meta:
        model = FieldType
        fields = ('id', 'name', 'field_type', 'classification')

    def create(self, validated_data):
        classification_data = validated_data.pop('fclass_set', {})
        instance = super().create(validated_data)
        instance.save()
        if classification_data and instance.field_type == FieldTypes.CLASSIFICATION:
            for classification in classification_data:
                fclass = FClass(order=classification['order'],
                                classification=instance,
                                value=classification['value'])
                fclass.save()
        return instance

    def update(self, instance, validated_data):
        classification_data = validated_data.pop('fclass_set', {})
        instance = super().update(instance, validated_data)
        if classification_data and instance.field_type == FieldTypes.CLASSIFICATION:
            classification_list = []
            for classification in classification_data:
                fclass = FClass(order=classification['order'],
                                classification=instance,
                                value=classification['value'])
                fclass.save()
                classification_list.append(fclass)
            classification_data_ids = [f.id for f in classification_list]
            for fclass in instance.fclass_set.all():
                if fclass.id not in classification_data_ids:
                    fclass.delete(keep_parents=True)
        return instance


class PlaceFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceField
        fields = ('id', 'attribute', 'unit', 'infrastructure',
                  'field_type', 'sensitive')
