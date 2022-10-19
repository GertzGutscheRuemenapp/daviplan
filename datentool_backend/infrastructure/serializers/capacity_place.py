import pandas as pd
from asgiref.sync import sync_to_async
from requests.exceptions import ConnectionError
from rest_framework.validators import ValidationError
from rest_framework import serializers

from datentool_backend.population.models import RasterCell
from datentool_backend.modes.models import ModeVariant, Mode
from datentool_backend.indicators.models import MatrixCellPlace
from datentool_backend.indicators.views.transit import TravelTimeRouterMixin
from datentool_backend.area.models import FClass, FieldTypes
from datentool_backend.infrastructure.models.places import (Place,
                                                            Capacity,
                                                            PlaceField,
                                                            )
from datentool_backend.utils.geometry_fields import GeometrySRIDField
from datentool_backend.infrastructure.models.infrastructures import (
    Infrastructure)


class CapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Capacity
        fields = ('id', 'place', 'service', 'capacity',
                  'from_year', 'scenario')


class CapacityAmountSerializer(serializers.FloatField):

    def to_representation(self, item) -> str:
        return super().to_representation(item.capacity)


class PlaceAttributeField(serializers.DictField):
    """remove sensitive fields if the user is not allowed to see them"""

    def get_attribute(self, instance):
        try:
            # use the prefetched data
            users_infra_access = instance.infrastructure.users_infra_access
        except AttributeError:
            # after put and post, no infra_access information is prefetched
            profile = self.context['request'].user.profile
            users_infra_access = instance.infrastructure.infrastructureaccess_set.filter(profile=profile)
        try:
            allow_sensitive_data = users_infra_access[0].allow_sensitive_data
        except IndexError:
            # if no infra_access is defined, allow only if user is admin
            allow_sensitive_data = self.context['request'].user.profile.admin_access

        attributes = {pa.field.name: pa.value
                      for pa in instance.placeattribute_set.all()
                      if allow_sensitive_data or not pa.field.sensitive}
        return attributes


class PlaceAttributeValidator:
    """validate the place attribute"""
    requires_context = True

    def __call__(self, value, field):
        """"""
        place: Place = field.parent.instance
        if place:
            infrastructure = place.infrastructure
        else:
            properties = field.parent.initial_data.get('properties')
            if properties:
                infrastructure_id = properties.get('infrastructure')
            else:
                infrastructure_id = field.parent.context['request'].data.get(
                    'infrastructure')
            if infrastructure_id is None:
                raise ValidationError('No infrastructure_id provided')
            infrastructure = Infrastructure.objects.get(pk=infrastructure_id)
        infr_name = infrastructure.name

        for field_name, field_value in value.items():
            # check if the fields exist as a PlaceField
            try:
                place_field = PlaceField.objects.get(
                    name__iexact=field_name,
                    infrastructure=infrastructure)
            except PlaceField.DoesNotExist:
                msg = f'Field {field_name} is no PlaceField for Infrastructure {infr_name}'
                raise ValidationError(msg)
            # check if the value is of correct type
            field_type = place_field.field_type
            if not field_type.validate_datatype(field_value):
                ft = FieldTypes(field_type.ftype)
                msg = f'''Field '{field_name}' for Infrastructure '{infr_name}'
                should be of {field_type}({ft.label})'''
                if field_type.ftype == FieldTypes.CLASSIFICATION:
                    fclasses = list(
                        FClass.objects.filter(ftype=field_type)\
                        .values_list('value', flat=True))
                    msg += f'.The value {field_value!r} is not in the valid classes {fclasses}.'
                else:
                    msg += f''', but the value is {field_value!r}.'''
                raise ValidationError(msg)


class PlaceSerializer(serializers.ModelSerializer):
    geom = GeometrySRIDField(srid=3857)
    attributes = PlaceAttributeField(validators=[PlaceAttributeValidator()])

    class Meta:
        model = Place
        fields = ('id', 'name', 'geom', 'infrastructure', 'attributes', 'scenario')

    def create(self, validated_data):
        instance = super().create(validated_data)
        # auto calc. travel times for scenario places
        if instance.scenario:
            sources = TravelTimeRouterMixin.annotate_coords(
                Place.objects.filter(pk=instance.pk), geom='geom')
            destinations = TravelTimeRouterMixin.annotate_coords(
                RasterCell.objects.filter(rastercellpopulation__isnull=False),
                geom='pnt')
            dataframes = []
            for variant in ModeVariant.objects.all():
                # ToDo: route transit
                if variant.mode == Mode.TRANSIT:
                    continue
                try:
                    df = TravelTimeRouterMixin.route(
                        variant, sources, destinations,
                        id_columns=['place_id', 'cell_id'])
                except ConnectionError:
                    return instance
                dataframes.append(df)
            df = pd.concat(dataframes)
            TravelTimeRouterMixin.save_df(df, MatrixCellPlace.objects.none(), False)
        return instance


class PlaceFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceField
        fields = ('id', 'name', 'unit', 'infrastructure', 'field_type', 'sensitive')


class PlaceFieldNestedSerializer(serializers.ModelSerializer):
    # id is explicitly needed here, otherwise it is not appearing
    # in the validated data
    id = serializers.IntegerField(required=False)
    class Meta:
        model = PlaceField
        fields = ('id', 'name', 'unit', 'field_type', 'sensitive')

