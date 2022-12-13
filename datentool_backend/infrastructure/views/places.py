from typing import Dict, Tuple
from io import StringIO
import logging
logger = logging.getLogger('infrastructure')

import pandas as pd

from django.core.exceptions import BadRequest
from django.contrib.gis.geos import Point
from django.db.models import Prefetch, Q
from django.http.request import QueryDict
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import (extend_schema,
                                   extend_schema_view,
                                   inline_serializer,
                                   )
from djangorestframework_camel_case.util import camelize

from djangorestframework_camel_case.parser import CamelCaseMultiPartParser
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.excel_template import (ExcelTemplateMixin,
                                                    write_template_df,
                                                    ColumnError,
                                                    )
from datentool_backend.utils.crypto import decrypt
from datentool_backend.utils.permissions import (HasAdminAccess,
                                                 HasAdminAccessOrReadOnly,
                                                 CanEditBasedata,
                                                 )

from datentool_backend.site.models import SiteSetting
from datentool_backend.utils.bkg_geocoder import BKGGeocoder

from datentool_backend.models import (
    InfrastructureAccess, Place, Infrastructure, Capacity, FClass,
    PlaceAttribute)

from datentool_backend.infrastructure.permissions import (
    CanEditScenarioPlacePermission)

from datentool_backend.infrastructure.serializers import (
    PlaceSerializer,
    PlacesTemplateSerializer,
    infrastructure_id_serializer)


@extend_schema_view(list=extend_schema(description='List Places',
                                       parameters=[]),
                    retrieve=extend_schema(description='Get Place with id'))
class PlaceViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):

    serializer_class = PlaceSerializer
    serializer_action_classes = {
        'create_template': PlacesTemplateSerializer,
        'upload_template': PlacesTemplateSerializer}
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata |
                          CanEditScenarioPlacePermission]
    filterset_fields = ['infrastructure']

    def create(self, request, *args, **kwargs):
        """use the annotated version"""
        attributes = request.data.get('attributes')
        request.data['attributes'] = camelize(attributes)
        serializer = self.get_serializer(data=request.data)
        # ToDo: return error response
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        #replace the created instance with an annotated instance
        serializer.instance = Place.objects.get(pk=serializer.instance.pk)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        attributes = request.data.get('attributes')
        request.data['attributes'] = camelize(attributes)
        return super().update(request, *args, **kwargs)

    def get_queryset(self):
        try:
            profile = self.request.user.profile
        except AttributeError:
            # no profile yet
            return Place.objects.none()
        accessible_infrastructure = InfrastructureAccess.objects.filter(profile=profile)

        queryset = Place.objects.select_related('infrastructure')\
            .prefetch_related(
                Prefetch('infrastructure__infrastructureaccess_set',
                         queryset=accessible_infrastructure,
                         to_attr='users_infra_access'),
                Prefetch('placeattribute_set',
                         queryset=PlaceAttribute.objects.select_related('field__field_type'))
                )

        return queryset

    # only filtering for list view
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        scenario = self.request.query_params.get('scenario')
        if scenario is not None:
            queryset = queryset.filter(Q(scenario=scenario) | Q(scenario__isnull=True))
        else:
            queryset = queryset.filter(scenario__isnull=True)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(description='Create Excel-Template to download',
                   request=inline_serializer(
                       name='PlaceCreateSerializer',
                       fields={'infrastructure': infrastructure_id_serializer}
                   ),
                   )
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccess | CanEditBasedata])
    def create_template(self, request):
        """Download the Template"""
        infrastructure_id = request.data.get('infrastructure')
        return super().create_template(request, infrastructure_id=infrastructure_id)

    @extend_schema(description='Upload Excel-File with Places and Capacities',
                   request=inline_serializer(
                       name='PlaceFileUploadSerializer',
                       fields={'excel_file': serializers.FileField(),}
                   ))
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccess | CanEditBasedata],
            parser_classes=[CamelCaseMultiPartParser])
    def upload_template(self, request):
        """Download the Template"""
        # no constraint dropping, because we use individual updates
        data = QueryDict(mutable=True)
        data.update(self.request.data)
        data['drop_constraints'] = 'False'
        request._full_data = data

        queryset = Place.objects.none()
        return super().upload_template(request,
                                       queryset=queryset,)

    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def clear(self, request, **kwargs):
        infrastructure_id = request.data.get('infrastructure')
        if (infrastructure_id is not None):
            places = Place.objects.filter(infrastructure=infrastructure_id)
        else:
            places = Place.objects.all()
        count = places.count()
        places.delete()
        return Response({'message': f'{count} Areas deleted'},
                        status=status.HTTP_200_OK)

    def get_read_excel_params(self, request) -> Dict:
        params = dict()
        params['excel_file'] = request.FILES['excel_file']
        params['infrastructure_id'] = request.data.get('infrastructure')
        return params

    @staticmethod
    def process_excelfile(queryset,
                          logger,
                          excel_file,
                          infrastructure_id,
                          drop_constraints=False,
                          ):
        # read excelfile
        assert infrastructure_id is not None, 'Die ID der Infrastruktur muss im Formular mit übergeben werden.'

        logger.info('Lese Excel-Datei')
        read_excel_file(excel_file, infrastructure_id)

        # write_df is skipped, because data is uploaded directly


def read_excel_file(excel_file, infrastructure_id: int):
    """read excelfile and return a dataframe"""
    infra = Infrastructure.objects.get(pk=infrastructure_id)

    # get the services and the place fields of the infrastructure
    services = infra.service_set.all().values('id', 'has_capacity', 'name')
    place_fields = infra.placefield_set.all().values('id',
                                                     'name',
                                                     'field_type',
                                                     'field_type__ftype',
                                                     'field_type__name',
                                                     )

    # get a mapping of the classifications
    fclass_values = FClass.objects\
        .filter(ftype__in=place_fields.values_list('field_type'))\
        .values('ftype', 'id', 'value')

    fclass_dict = {(fclass_value['ftype'], fclass_value['value']):
                   fclass_value['id']
                   for fclass_value in fclass_values}

    # collect the places, attributes and capacities in lists
    place_ids = []
    place_attributes = []
    capacities = []

    # read the excel-file
    df_places = pd.read_excel(excel_file.file,
                       sheet_name='Standorte und Kapazitäten',
                       skiprows=[1])\
        .set_index('place_id')

    # delete places that have no place_id in the excel-file
    place_ids_in_excelfile = df_places.index[~pd.isna(df_places.index)]
    places_to_delete = Place.objects.filter(infrastructure=infrastructure_id)\
        .exclude(id__in=place_ids_in_excelfile)
    n_elems_deleted, elems_deleted = places_to_delete.delete()
    n_places_deleted = elems_deleted.get('datentool_backend.Place')
    logger.info(f'{n_places_deleted or 0} bestehende Standorte gelöscht')

    # get BKG-Geocoding-Key
    site_settings = SiteSetting.load()
    UUID = site_settings.bkg_password or None
    bkg_error = ('Es wurde keine UUID für die Nutzung des BKG-'
                 'Geokodierungsdienstes hinterlegt' if not UUID else '')
    geocoder = None
    if UUID:
        try:
            bkg_pass = decrypt(UUID)
        except Exception:
            bkg_error = ('Die UUID des BKG-Geokodierungsdienstes konnte '
                         'nicht entschlüsselt werden. Vermutlich ist der '
                         'hinterlegte Schlüssel (ENCRYPT_KEY) nicht valide '
                         '(URL-safe base64-encoded 32-byte benötigt)')
        else:
            geocoder = BKGGeocoder(bkg_pass, crs='EPSG:3857')

    # iterate over all places
    n_new = 0
    for place_id, place_row in df_places.iterrows():
        if pd.isna(place_id):
            place_id = None
        # check if place_id exists, otherwise create it
        try:
            place = Place.objects.get(pk=place_id)
        except Place.DoesNotExist:
            place = Place()
            n_new += 1

        place_name = place_row['Name']
        if pd.isna(place_name):
            place_name = ''

        #  do a geocoding, if no coordinates are provided
        lon = place_row['Lon']
        lat = place_row['Lat']
        if pd.isna(lon) or pd.isna(lat):
            if geocoder:
                # ToDo: handle auth errors ...
                logger.info('Geokodiere Adressen')
                res = geocode(geocoder, place_row)
                if res:
                    lon, lat = res
                    geom = Point(lon, lat, srid=3857)
                else:
                    logger.error(f'''Konnte Adresse für {place_row.Name} mit folgender Adresse nicht finden:
                    Ort: {place_row.Ort}, PLZ: {place_row.PLZ}, strasse: {place_row.Straße}, Haus: {place_row.Hausnummer}''')
                    continue
            else:
                from django.core.exceptions import ValidationError
                raise ValidationError(bkg_error)
        else:
            # create the geometry and transform to WebMercator
            geom = Point(lon, lat, srid=4326)
            geom.transform(3857)

        # set the place columns
        place.infrastructure = infra
        place.name = place_name
        place.geom = geom
        place.save()
        place_ids.append(place.id)

        # collect the place_attributes
        for place_field in place_fields:
            place_field_name = place_field['name']
            attr = place_row.get(place_field_name)
            if attr and not pd.isna(attr):
                str_value, num_value, class_value = None, None, None
                ftype = place_field['field_type__ftype']
                if ftype == 'STR':
                    str_value = attr
                elif ftype == 'NUM':
                    num_value = float(attr)
                else:
                    try:
                        class_value = fclass_dict[(place_field['field_type'],
                                                   attr)]
                    except KeyError:
                        fieldtype_name = place_field['field_type__name']
                        msg = f'Wert {attr} existiert nicht für Klassifizierung '\
                            f'{fieldtype_name} in Spalte {place_field_name}'
                        raise ColumnError(msg)
                attribute = (place.id, place_field['id'], str_value, num_value, class_value)
                place_attributes.append(attribute)

        # collect the capacities
        for service in services:
            service_name = service['name']
            if service['has_capacity']:
                col = f'Kapazität für Leistung {service_name}'
            else:
                col = f'Bietet Leistung {service_name} an'
            capacity = place_row.get(col)
            if capacity is not None and not pd.isna(capacity):
                capacities.append((place.id, service['id'], capacity, 0, 99999999))

    # upload the place-attributes
    df_place_attributes = pd.DataFrame(place_attributes, columns=[
        'place_id', 'field_id', 'str_value', 'num_value', 'class_value_id'
    ])

    df_place_attributes['class_value_id'] = df_place_attributes['class_value_id'].astype('Int64')

    existing_place_attrs = PlaceAttribute.objects.filter(place_id__in=place_ids)
    existing_place_attrs.delete()

    if len(df_place_attributes):
        with StringIO() as file:
            df_place_attributes.to_csv(file, index=False)
            file.seek(0)
            PlaceAttribute.copymanager.from_csv(
                file,
                drop_constraints=False, drop_indexes=False,
            )

    # upload the capacities
    df_capacities = pd.DataFrame(capacities,
                                 columns=['place_id', 'service_id', 'capacity',
                                          'from_year', 'to_year'])

    existing_capacities = Capacity.objects.filter(place_id__in=place_ids)
    existing_capacities.delete()

    if len(df_capacities):
        with StringIO() as file:
            df_capacities.to_csv(file, index=False)
            file.seek(0)
            Capacity.copymanager.from_csv(
                file,
                drop_constraints=False, drop_indexes=False,
            )
    logger.info(f'{len(df_places)} Einträge bearbeitet')
    if n_new > 0:
        logger.info(f'davon {n_new} als neue Orte hinzugefügt')
        logger.info('ACHTUNG: Für die neuen Orte muss die '
                         'Erreichbarkeit neu berechnet werden!')

def geocode(geocoder: BKGGeocoder, place_row: dict) -> Tuple[float, float]:
    kwargs = {
        'ort': place_row.Ort,
        'plz': place_row.PLZ,
        'strasse': place_row.Straße,
        'haus': place_row.Hausnummer,
    }
    res = geocoder.query(max_retries=2, **kwargs)
    if res.status_code != 200:
        return
    features = res.json()['features']
    if not features:
        return
    return features[0]['geometry']['coordinates']
