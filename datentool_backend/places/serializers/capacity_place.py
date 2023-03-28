import logging
logger = logging.getLogger('routing')

from typing import List
import pandas as pd
from requests.exceptions import ConnectionError
from rest_framework.validators import ValidationError
from rest_framework import serializers

from datentool_backend.utils.raw_delete import delete_chunks
from datentool_backend.population.models import RasterCell
from datentool_backend.modes.models import (ModeVariant,
                                            Mode,
                                            DEFAULT_MAX_DIRECT_WALKTIME,
                                            MODE_MAX_DISTANCE,
                                            get_default_access_variant)
from datentool_backend.indicators.models import MatrixCellPlace, MatrixPlaceStop
from datentool_backend.indicators.compute.routing import (MatrixCellPlaceRouter,
                                                          MatrixPlaceStopRouter,
                                                          RoutingError)
from datentool_backend.indicators.models import Stop
from datentool_backend.area.models import FClass, FieldTypes
from datentool_backend.places.models import (Place,
                                             Capacity,
                                             PlaceField,
                                             )
from datentool_backend.utils.geometry_fields import GeometrySRIDField
from datentool_backend.infrastructure.models import Infrastructure


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
        user = self.context['request'].user
        if user.is_superuser or user.profile.admin_access:
            allow_sensitive_data = True
        else:
            try:
                # use the prefetched data
                users_infra_access = instance.infrastructure.users_infra_access
            except AttributeError:
                # after put and post, no infra_access information is prefetched
                profile = user.profile
                users_infra_access = instance.infrastructure.infrastructureaccess_set.filter(profile=profile)
            try:
                allow_sensitive_data = users_infra_access[0].allow_sensitive_data
            except IndexError:
                allow_sensitive_data = False

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

    def create(self, validated_data: dict) -> Place:
        instance = super().create(validated_data)
        # auto calc. travel times for scenario places
        if instance.scenario:
            self.calc_traveltimes_for_place(instance)
        return instance

    def calc_traveltimes_for_place(self, instance: Place):
        places = MatrixCellPlaceRouter.annotate_coords(
            Place.objects.filter(pk=instance.pk), geom='geom')
        cells = MatrixCellPlaceRouter.annotate_coords(
            RasterCell.objects.filter(rastercellpopulation__isnull=False),
            geom='pnt')
        access_variant = ModeVariant.objects.get(pk=get_default_access_variant())
        model_name = MatrixCellPlace._meta.object_name

        self.delete_existing_martixentries_for_place(instance)

        # calcauats
        for variant in ModeVariant.objects.order_by('mode'):
            try:
                if variant.mode == Mode.TRANSIT:
                    df = self.get_transit_df(variant, access_variant, places)
                else:
                    df = self.get_prt_df(variant, places, cells)

                n_inserted = len(df)
                if not n_inserted:
                    continue
                print(f'Routing für Modus {repr(variant)}: {n_inserted:n} Relationen gefunden')
                MatrixCellPlace.add_n_rels(df)
                MatrixCellPlaceRouter.save_df(df, MatrixCellPlace, False)
                print(f'{n_inserted:n} {model_name}-Einträge geschrieben')

            except (ConnectionError, RoutingError):
                print(f'Routing für {variant.label} hat nicht funktioniert')

        print(f'Routenberechnung erfolgreich')

    def delete_existing_martixentries_for_place(self, instance: Place):
        # delete existing entries for the place in the CellPlace and PlaceStop-Matrix
        qs_to_delete = MatrixCellPlace.objects.filter(place=instance)
        if qs_to_delete.exists():
            delete_chunks(qs_to_delete, logger)
        qs_to_delete = MatrixPlaceStop.objects.filter(place=instance)
        if qs_to_delete.exists():
            delete_chunks(qs_to_delete, logger)

    def update(self, instance: Place, validated_data: dict) -> Place:
        geom = validated_data.get('geom')
        instance = super().update(instance, validated_data)
        if geom:
            self.calc_traveltimes_for_place(instance)
        return instance

    def get_prt_df(self,
                   variant: ModeVariant,
                   places: List[Place],
                   cells: List[RasterCell]) -> pd.DataFrame:
        chunk_size = 10000
        max_distance = MODE_MAX_DISTANCE[variant.mode]
        cell_ids = cells.values_list('id')
        dataframes = []
        for i in range(0, len(cells), chunk_size):
            dest_part = cells.filter(
                id__in=cell_ids[i:i + chunk_size])
            df = MatrixCellPlaceRouter.route(variant,
                                             sources=places,
                                             destinations=dest_part,
                                             logger=logger,
                                             max_distance=max_distance,
                                             id_columns=MatrixCellPlaceRouter.columns)
            dataframes.append(df)
        if dataframes:
            df = pd.concat(dataframes)
        else:
            df = pd.DataFrame(columns=['place_id', 'cell_id', 'minutes',
                                       'access_variant_id', 'variant_id'])

        df, ignore_columns = MatrixCellPlaceRouter.add_partition_key(
            df,
            variant_id=variant.pk,
            places=places.values_list('id'))
        df.drop(ignore_columns, axis=1, inplace=True)
        return df

    def get_transit_df(self,
                       variant: ModeVariant,
                       access_variant: ModeVariant,
                       places: List[Place]) -> pd.DataFrame:
        """get the dataframe for transit """
        # get the stops of the transit-variant
        # and add coordinates in WGS84
        stops = MatrixPlaceStopRouter.annotate_coords(
            Stop.objects.filter(variant=variant), geom='geom')
        if not stops:
            return pd.DataFrame()
        max_access_distance = float(MODE_MAX_DISTANCE[variant.mode])
        # calculate access time from the new place to the stops
        chunk_size = 10000
        dataframes = []
        stops_ids = stops.values_list('id')
        for i in range(0, len(stops), chunk_size):
            dest_part = stops.filter(
                id__in=stops_ids[i:i + chunk_size])
            df = MatrixPlaceStopRouter.route(
                variant=access_variant,
                sources=places,
                destinations=dest_part,
                logger=logger,
                max_distance=max_access_distance,
                id_columns=MatrixPlaceStopRouter.columns)

            dataframes.append(df)
        df_ps = pd.concat(dataframes)

        df_ps.rename(
            columns={'variant_id': 'access_variant_id', },
            inplace=True)
        MatrixPlaceStop.add_n_rels_for_variant(variant.pk, len(df_ps))

        df_ps, ignore_columns = MatrixPlaceStopRouter.add_partition_key(
            df_ps,
            transit_variant_id=variant.pk,
            places=places.values_list('id'))
        df_ps.drop(ignore_columns, axis=1, inplace=True)

        #df_ps['transit_variant_id'] = variant.pk
        # add the access times to the database
        MatrixPlaceStopRouter.save_df(df_ps,
                                      MatrixPlaceStop,
                                      drop_constraints=False)

        # calc the shortest transit time from the new stop via the
        # access stops to all cells
        df = MatrixCellPlaceRouter.calculate_transit_traveltime(
            transit_variant=variant,
            access_variant=access_variant,
            max_direct_walktime=DEFAULT_MAX_DIRECT_WALKTIME,
            places=places.values_list('id', flat=True),
            id_columns=MatrixCellPlaceRouter.columns)

        df, ignore_columns = MatrixCellPlaceRouter.add_partition_key(
            df,
            variant_id=variant.pk,
            places=places.values_list('id'))

        df.drop(ignore_columns, axis=1, inplace=True)

        return df


class PlaceFieldListSerializer(serializers.ListSerializer):
    '''
    only list fields the requesting user has access to (not sensitive or in
    an infrastructure marked as allowed for her/him)
    '''
    def to_representation(self, data):
        user = self.context['request'].user
        if (user.is_superuser or user.profile.admin_access):
            return super().to_representation(data)
        accessible_data = []
        for infrastructure_id in data.values_list(
            'infrastructure', flat=True).distinct():
            infrastructure = Infrastructure.objects.get(id=infrastructure_id)
            users_infra_access = infrastructure.infrastructureaccess_set.filter(
                profile=user.profile)
            allow_sensitive_data = users_infra_access[0].allow_sensitive_data \
                if users_infra_access else False
            fields = data.filter(infrastructure=infrastructure)
            for field in fields:
                if not field.sensitive or allow_sensitive_data:
                    accessible_data.append(field)
        return super().to_representation(accessible_data)


class PlaceFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceField
        list_serializer_class = PlaceFieldListSerializer
        fields = ('id', 'name', 'label', 'unit', 'infrastructure',
                  'field_type', 'sensitive')


class PlaceFieldNestedSerializer(serializers.ModelSerializer):
    # id is explicitly needed here, otherwise it is not appearing
    # in the validated data
    id = serializers.IntegerField(required=False)
    class Meta:
        list_serializer_class = PlaceFieldListSerializer
        model = PlaceField
        fields = ('id', 'name', 'label', 'unit', 'field_type', 'sensitive',
                  'is_preset')


class ServiceCapacityByScenarioSerializer(serializers.Serializer):
    scenario_id = serializers.IntegerField()
    n_places = serializers.IntegerField()
    total_capacity = serializers.FloatField()
