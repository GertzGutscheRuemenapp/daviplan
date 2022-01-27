import json
from rest_framework.validators import ValidationError
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework.fields import JSONField, empty

from .models import (Scenario,
                     ScenarioMode,
                     ScenarioService,
                     FieldType,
                     FClass,
                     FieldTypes,
                     Place,
                     Capacity,
                     PlaceField,
                     )
from datentool_backend.utils.geometry_fields import GeometrySRIDField
from datentool_backend.user.models import (Infrastructure,
                                           InfrastructureAccess,
                                           )


class ScenarioModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioMode
        fields = ('mode', 'variant')


class ScenarioDemandRateSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioService
        fields = ('service', 'demandrateset')


class ScenarioSerializer(serializers.ModelSerializer):
    modevariants = ScenarioModeSerializer(
        many=True, source='scenariomode_set', required=False)
    demandratesets = ScenarioDemandRateSetSerializer(
        many=True, source='scenarioservice_set', required=False)

    class Meta:
        model = Scenario
        fields = ('id', 'name', 'planning_process', 'prognosis',
                  'modevariants', 'demandratesets')

    def update(self, instance, validated_data):
        mode_set = validated_data.pop('scenariomode_set', [])
        service_set = validated_data.pop('scenarioservice_set', [])
        super().update(instance, validated_data)

        ## delete
        #existing_scenario_modes\
            #.exclude(id__in=[m.mode for m in modevariants])\
            #.delete()

        #  delete all and recreate
        existing_scenario_modes = ScenarioMode.objects.filter(scenario=instance)
        existing_scenario_modes.delete()
        for mode in mode_set:
            ScenarioMode.objects.create(scenario=instance,
                                        mode=mode['mode'],
                                        variant=mode['variant'])

        #  delete all and recreate
        existing_scenario_service = ScenarioService.objects.filter(scenario=instance)
        existing_scenario_service.delete()
        for service in service_set:
            ScenarioService.objects.create(scenario=instance,
                                           service=service['service'],
                                           demandrateset=service['demandrateset'])

        return instance

    def create(self, validated_data):
        mode_set = validated_data.pop('scenariomode_set', [])
        service_set = validated_data.pop('scenarioservice_set', [])
        instance = super().create(validated_data)
        for mode in mode_set:
            ScenarioMode.objects.create(scenario=instance,
                                        mode=mode['mode'],
                                        variant=mode['variant'])
        for service in service_set:
            ScenarioService.objects.create(scenario=instance,
                                           service=service['service'],
                                           demandrateset=service['demandrateset'])
        return instance



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
            service_ids = request.query_params.getlist('service')
            year = request.query_params.get('year', 0)
            scenario = request.query_params.get('scenario')

            instance = Capacity.filter_queryset(instance,
                                                service_ids=service_ids,
                                                scenario_id=scenario,
                                                year=year)

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
