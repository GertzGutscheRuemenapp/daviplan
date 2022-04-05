import requests
from requests.exceptions import (MissingSchema, ConnectionError, HTTPError)
from distutils.util import strtobool
import pandas as pd
import json
from owslib.wfs import WebFeatureService
import datetime

from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.views.generic import DetailView
from django.http import JsonResponse
from django.db.models import OuterRef, Subquery, CharField, Case, When, F, JSONField, Func
from django.db.models.functions import Cast
from django.contrib.postgres.aggregates import ArrayAgg
from django_filters import rest_framework as filters

from rest_framework.response import Response
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.exceptions import (ParseError, NotFound, APIException)
from rest_framework.decorators import action
from drf_spectacular.utils import (extend_schema,
                                   OpenApiResponse,
                                   inline_serializer)

from owslib.wms import WebMapService

from vectortiles.postgis.views import MVTView, BaseVectorTileView
from drf_spectacular.utils import extend_schema

from datentool_backend.utils.serializers import (drop_constraints,
                                                 MessageSerializer)
from datentool_backend.population.models import (PopulationRaster, AreaCell,
                                                 Population)
from datentool_backend.population.views import aggregate_population
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.utils.pop_aggregation import (
    intersect_areas_with_raster, aggregate_population)

from .models import (MapSymbol,
                     LayerGroup,
                     WMSLayer,
                     AreaLevel,
                     Area,
                     FieldType,
                     FClass,
                     AreaAttribute,
                     FieldTypes,
                     SourceTypes
                     )
from .serializers import (MapSymbolSerializer,
                          LayerGroupSerializer,
                          WMSLayerSerializer,
                          GetCapabilitiesRequestSerializer,
                          GetCapabilitiesResponseSerializer,
                          AreaLevelSerializer,
                          AreaSerializer,
                          FieldTypeSerializer,
                          FClassSerializer,
                          )
from datentool_backend.site.models import ProjectSetting


class JsonObject(Func):
    function = 'json_object'
    output_field = JSONField()


class AreaLevelTileView(MVTView, DetailView):
    model = AreaLevel
    vector_tile_fields = ('id', 'area_level', 'attributes', 'label')

    def get_vector_tile_layer_name(self):
        return self.get_object().name

    def get_vector_tile_queryset(self):
        areas = self.get_object().area_set.all()
        # annotate the areas
        return self.annotate_areas_with_label_and_attributes(areas)

    def annotate_areas_with_label_and_attributes(self, areas):
        """annotate the areas with label and attributes"""
        sq = AreaAttribute.objects.filter(area=OuterRef('pk'))

        # get the area attributes
        sq = sq.annotate(val=Case(
            When(field__field_type__ftype=FieldTypes.STRING, then=F('str_value')),
            When(field__field_type__ftype=FieldTypes.NUMBER, then=Cast(F('num_value'), CharField())),
            When(field__field_type__ftype=FieldTypes.CLASSIFICATION,
                 then=F('class_value__value')),
            output_field=CharField())
                         )

        # annotate the label
        sq_label = sq.filter(field__is_label=True)\
            .values('val')

        # annotate the attributes in json-format
        sq_attrs = sq.values('area')\
            .annotate(attributes=JsonObject(ArrayAgg(F('field__name')),
                                            ArrayAgg(F('val')),
                                            output_field=CharField()))\
            .values('attributes')

        # annotate attributes and label to the queryset
        areas = areas\
            .annotate(attributes=Subquery(sq_attrs, output_field=CharField()))\
            .annotate(label=Subquery(sq_label, output_field=CharField()))

        return areas

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return BaseVectorTileView.get(self, request=request, z=kwargs.get('z'),
                                      x=kwargs.get('x'), y=kwargs.get('y'))


class MapSymbolsViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = MapSymbol.objects.all()
    serializer_class = MapSymbolSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class LayerGroupViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = LayerGroup.objects.all()
    serializer_class = LayerGroupSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filter_fields = ['external']


class WMSLayerViewSet(viewsets.ModelViewSet):
    queryset = WMSLayer.objects.all()
    serializer_class = WMSLayerSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filter_fields = ['active']

    @extend_schema(
        description='Get capabilites of WMS-Service',
        request=GetCapabilitiesRequestSerializer,
        responses=GetCapabilitiesResponseSerializer,
    )
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def getcapabilities(self, request, **kwargs):
        url = request.data.get('url')
        version = request.data.get('version', '1.3.0')
        if not url:
            raise ParseError('keine URL angegeben')
        try:
            wms = WebMapService(url, version=version)
        except MissingSchema:
            raise ParseError(
                'ungültiges URL-Schema (http:// bzw. https:// vergessen?)')
        except ConnectionError:
            raise NotFound('URL nicht erreichbar')
        except HTTPError as e:
            raise APIException(str(e))
        except Exception:
            raise APIException('ein Fehler ist bei der Abfrage der '
                               'Capabilities aufgetreten')

        layers = []
        for layer_name, layer in wms.contents.items():
            layers.append({
                'name':  layer_name,
                'title': layer.title,
                'abstract': layer.abstract,
                'bbox': layer.boundingBoxWGS84,
            })

        # test for anonymous CORS-support
        headers = {
            "Origin": "*",
            "Referer": "*",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        res = requests.options(url, headers=headers)
        cors_enabled = ('access-control-allow-origin' in res.headers and
                        res.headers['access-control-allow-origin'] == '*')

        return JsonResponse({
            'version': wms.version,
            'layers': layers,
            'url': wms.url,
            'cors': cors_enabled
        })


class ProtectPresetPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # presets can not be deleted and name, label and
        # source type (except date) can not be changed
        if (obj.is_preset and
            (
                request.method == 'DELETE' or
                'name' in request.data or
                'label_field' in request.data or
                'key_field' in request.data or
                (
                    'source' in request.data and
                    set(request.data['source']) > set(['date'])
                )
            )):
            return False
        return True


class AreaLevelFilter(filters.FilterSet):
    active = filters.BooleanFilter(field_name='is_active')
    class Meta:
        model = AreaLevel
        fields = ['is_active']


class AreaLevelViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = AreaLevel.objects.all()
    serializer_class = AreaLevelSerializer
    permission_classes = [ProtectPresetPermission &
                          (HasAdminAccessOrReadOnly | CanEditBasedata)]
    filterset_class = AreaLevelFilter

    @extend_schema(description='intersect areas of area level with rastercells',
                   request=inline_serializer(
                       name='IntersectAreaSerializer',
                       fields={
                           'drop_constraints': drop_constraints,
                           'pop_raster': serializers.IntegerField(
                               required=False,
                               help_text='''population raster to intersect areas of
                               area level with, defaults to first raster found '''),
                       }
                   ),
                   responses={
                       202: OpenApiResponse(MessageSerializer, 'Intersection successful'),
                       406: OpenApiResponse(MessageSerializer, 'Intersection failed')
                   })
    @action(methods=['POST'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def intersect_areas(self, request, **kwargs):
        """
        route to intersect areas with raster cells
        """
        try:
            area_level: AreaLevel = self.queryset.get(**kwargs)
        except AreaLevel.DoesNotExist:
            msg = f'Area level for {kwargs} not found'
            return Response({'message': msg,}, status.HTTP_406_NOT_ACCEPTABLE)

        areas = Area.objects.filter(area_level=area_level)\
            .values_list('pk', flat=True)

        if not areas:
            return Response({'message': 'No areas available', },
                            status=status.HTTP_202_ACCEPTED)

        raster_id = request.data.get('pop_raster')
        raster = PopulationRaster.objects.get(id=raster_id) \
            if raster_id is not None else None

        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        intersect_areas_with_raster(areas, pop_raster=raster,
                                    drop_constraints=drop_constraints)

        msg = f'{len(areas)} Areas were successfully intersected with Rastercells.\n'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(description='Pull areas of area level incl. geometries '
                   'from assigned WFS-service ("source")',
                   request=inline_serializer(
                       name='PullAreaSerializer',
                       fields={
                           'simplify': serializers.BooleanField(
                               required=False,
                               help_text='simplify the fetched geometries'),
                           'truncate': serializers.BooleanField(
                               required=False,
                               help_text='''drop all existing areas if true.
                               Otherwise update existing areas with same key field
                               values resp. add new ones.'''),
                       }
                   ),
                   responses={
                       202: OpenApiResponse(MessageSerializer, 'Pull successful'),
                       406: OpenApiResponse(MessageSerializer, 'Pull failed'),
                       500: OpenApiResponse(MessageSerializer, 'Pull failed')
                   })
    @action(methods=['POST'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def pull_areas(self, request, **kwargs):
        # minimum area of feature in m² after intersection with project area
        # otherwise ignored
        MIN_AREA = 100000
        # percentage of intersected area in relation to original geometry
        # if above threshold uncut original geometry is taken
        INTERSECT_THRESHOLD = 0.95
        CUT_OUT_SUFFIX = '(Ausschnitt)'
        try:
            area_level: AreaLevel = self.queryset.get(**kwargs)
        except AreaLevel.DoesNotExist:
            msg = f'Area level for {kwargs} not found'
            return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)
        if (not area_level.source or
            area_level.source.source_type != SourceTypes.WFS):
            msg = 'Source of Area Level has to be a Feature-Service to pull from'
            return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)
        url = area_level.source.url
        layer = area_level.source.layer
        if not url or not layer:
            msg = 'Source of Area Level is not completely defined'
            return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)

        project_area = ProjectSetting.load().project_area
        if not project_area:
            msg = 'Project area is not defined'
            return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)
        # project bbox with srs
        bbox = list(project_area.extent)
        bbox.append('EPSG:3857')

        wfs = WebFeatureService(url=url, version='1.1.0')
        typename = None
        # find layer in available item
        for key, l in wfs.items():
            # name space might be missing in definition
            if key == layer or key.split(':')[-1] == layer:
                typename = key
                break
        if not key:
            msg = 'Layer not found in capabilities of service'
            return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)
        try:
            response = wfs.getfeature(typename=typename, bbox=bbox,
                                      srsname='EPSG:3857',
                                      outputFormat='application/json')
        except Exception as e:
            return Response({'message': str(e)},
                            status.HTTP_500_INTERNAL_SERVER_ERROR)
        res_json = json.loads(response.read())
        truncate = request.data.get('truncate', 'false').lower() == 'true'
        if truncate:
            Area.objects.filter(area_level=area_level).delete()
        simplify = request.data.get('simplify', 'false').lower() == 'true'
        level_areas = Area.annotated_qs(area_level)
        key_field = area_level.key_field
        label_field = area_level.label_field
        for feature in res_json['features']:
            properties = feature.get('properties', {})
            # ToDo: this only temporary, in case of presets (=bkg wfs)
            # only take land and ignore water parts, should be handled
            # differently, e.g. source params
            if area_level.is_preset and properties['gf'] != 4:
                continue
            geom = GEOSGeometry(str(feature['geometry']))
            geom.srid = 3857
            intersection = project_area.intersection(geom)
            if (intersection.area < MIN_AREA):
                continue
            if (intersection.area / geom.area > INTERSECT_THRESHOLD):
                intersection = geom
            if label_field and intersection.area < geom.area:
                properties[label_field] = (f'{properties.get(label_field, "")} '
                                           f'{CUT_OUT_SUFFIX}')
            # ToDo: do simplification in database after all features are put in?
            if (simplify):
                intersection = intersection.simplify(10, preserve_topology=True)
            if isinstance(intersection, Polygon):
                intersection = MultiPolygon(intersection)
            if not truncate and key_field and properties.get(key_field):
                existing = level_areas.filter(
                    **{key_field: properties.get(key_field)})
            else:
                existing = None
            if existing:
                area = existing[0]
                area.geom = intersection
                area.save()
            else:
                area = Area.objects.create(area_level=area_level,
                                           geom=intersection)
            area.attributes = properties
        # ToDo: call intersect_areas with raster, disaggregate, aggregate?
        now = datetime.datetime.now()
        area_level.source.date = datetime.date(now.year, now.month, now.day)
        area_level.source.save()
        areas = Area.objects.filter(area_level=area_level)
        intersect_areas_with_raster(areas, drop_constraints=True)
        for population in Population.objects.all():
            aggregate_population(area_level, population, drop_constraints=True)
        return Response({'message': f'{areas.count()} Areas pulled into database'},
                        status.HTTP_202_ACCEPTED)


class AreaViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filter_fields = ['area_level']


class FieldTypeViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = FieldType.objects.all()  # prefetch_related('classification_set',
                                         #         to_attr='classifications')
    serializer_class = FieldTypeSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class FClassViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = FClass.objects.all()
    serializer_class = FClassSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


