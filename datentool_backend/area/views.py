import requests
import tempfile
from requests.exceptions import (MissingSchema, ConnectionError, HTTPError)
import datetime
import json
import logging

from django.core.exceptions import BadRequest
from django.contrib.gis.geos import (Polygon, MultiPolygon, GEOSGeometry,
                                     GeometryCollection)
from django.views.generic import DetailView
from django.http import JsonResponse, Http404
from django.db.models import OuterRef, Subquery, CharField, Case, When, F, JSONField, Func
from django.db.models.functions import Cast
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.gis.gdal import field as gdal_field
from django.contrib.gis.gdal.error import GDALException
from django_filters import rest_framework as filters

from djangorestframework_camel_case.parser import CamelCaseMultiPartParser
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.exceptions import (ParseError, NotFound, APIException)
from rest_framework.decorators import action
from drf_spectacular.utils import (extend_schema,
                                   OpenApiParameter,
                                   OpenApiResponse,
                                   inline_serializer)

from owslib.wfs import WebFeatureService
from owslib.wms import WebMapService

from vectortiles.postgis.views import MVTView, BaseVectorTileView
from drf_spectacular.utils import extend_schema

from datentool_backend.utils.serializers import (drop_constraints,
                                                 MessageSerializer)
from datentool_backend.population.models import (PopulationRaster,
                                                 Population)
from datentool_backend.population.views import aggregate_population
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.utils.processes import ProtectedProcessManager
from datentool_backend.utils.pop_aggregation import (
    intersect_areas_with_raster, aggregate_population)
from datentool_backend.utils.layermapping import CustomLayerMapping

from .models import (MapSymbol,
                     LayerGroup,
                     WMSLayer,
                     AreaLevel,
                     Area,
                     FieldType,
                     FClass,
                     AreaAttribute,
                     FieldTypes,
                     AreaField,
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
                          AreaFieldSerializer,
                          )
from datentool_backend.site.models import ProjectSetting

logger = logging.getLogger('areas')


class JsonObject(Func):
    function = 'json_object'
    output_field = JSONField()


class AnnotatedAreasMixin:
    def annotate_areas_with_label_and_attributes(self, areas: Area):
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

        # annotate the key
        sq_key = sq.filter(field__is_key=True)\
            .values('val')

        # annotate the attributes in json-format
        sq_attrs = sq.values('area')\
            .annotate(attributes=JsonObject(ArrayAgg(F('field__name')),
                                            ArrayAgg(F('val')),
                                            output_field=CharField()))\
            .values('attributes')

        # annotate attributes and label and key to the queryset
        areas = areas\
            .annotate(attributes=Subquery(sq_attrs, output_field=CharField()))\
            .annotate(_label=Subquery(sq_label, output_field=CharField()))\
            .annotate(_key=Subquery(sq_key, output_field=CharField()))

        return areas


class AreaLevelTileView(AnnotatedAreasMixin, MVTView, DetailView):
    model = AreaLevel
    vector_tile_fields = ('id', 'area_level', 'attributes', '_label', '_key')

    def get_vector_tile_layer_name(self):
        return self.get_object().name

    def get_vector_tile_queryset(self):
        areas = self.get_object().area_set.all()
        # annotate the areas
        return self.annotate_areas_with_label_and_attributes(areas)

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
                'ftype' in request.data or
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


# minimum area of feature in m² after intersection with project area
# otherwise ignored
MIN_AREA = 10000
# percentage of intersected area in relation to original geometry
# if above threshold uncut original geometry is taken
INTERSECT_THRESHOLD = 0.95

class AreaLevelViewSet(AnnotatedAreasMixin,
                       ProtectCascadeMixin,
                       viewsets.ModelViewSet):
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

        drop_constraints = request.data.get('drop_constraints', False)

        intersect_areas_with_raster(areas, pop_raster=raster,
                                    drop_constraints=drop_constraints)

        msg = f'{len(areas)} Areas were successfully intersected with Rastercells.\n'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

    @staticmethod
    def _pull_areas(area_level: AreaLevel, project_area,
                   truncate=False, simplify=False):

        url = area_level.source.url
        layer = area_level.source.layer
        if not url or not layer:
            return []
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
        response = wfs.getfeature(typename=typename, bbox=bbox,
                                  srsname='EPSG:3857',
                                  outputFormat='application/json')
        res_json = json.loads(response.read())
        if truncate:
            Area.objects.filter(area_level=area_level).delete()
        level_areas = Area.annotated_qs(area_level)
        key_field = area_level.key_field
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
            # ToDo: do simplification in database after all features are put in?
            if (simplify):
                intersection = intersection.simplify(10, preserve_topology=True)
            if isinstance(intersection, Polygon):
                intersection = MultiPolygon(intersection)
            if isinstance(intersection, GeometryCollection):
                polys = []
                for geometry in intersection:
                    if isinstance(geometry, Polygon):
                        polys.append(geometry)
                intersection = MultiPolygon(polys)
            if not truncate and key_field and properties.get(key_field):
                existing = level_areas.filter(
                    **{key_field: properties.get(key_field)})
            else:
                existing = None
            is_cut = intersection.area < geom.area
            if existing:
                area = existing[0]
                area.geom = intersection
                area.is_cut = is_cut
                area.save()
            else:
                area = Area.objects.create(area_level=area_level, is_cut=is_cut,
                                           geom=intersection)
            area.attributes = properties
        now = datetime.datetime.now()
        area_level.source.date = datetime.date(now.year, now.month, now.day)
        area_level.source.save()
        areas = Area.objects.filter(area_level=area_level)
        return areas

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
        import time
        for i in range(10):
            logger.error(i)
            time.sleep(1)
        return Response({'message': ''}, status.HTTP_200_OK)
        try:
            area_level: AreaLevel = self.queryset.get(**kwargs)
        except AreaLevel.DoesNotExist:
            msg = f'Area level for {kwargs} not found'
            logger.error(msg)
            return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)
        if (not area_level.source or
            area_level.source.source_type != SourceTypes.WFS):
            msg = 'Source of Area Level has to be a Feature-Service to pull from'
            return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)
        if not area_level.source.url or not area_level.source.layer:
            msg = 'Source of Area Level is not completely defined'
            return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)
        project_area = ProjectSetting.load().project_area
        if not project_area:
            msg = 'Project area is not defined'
            return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)

        truncate = str(request.data.get('truncate', 'false')).lower() == 'true'
        simplify = str(request.data.get('simplify', 'false')).lower() == 'true'
        areas = self._pull_areas(area_level, project_area,
                                 truncate=truncate, simplify=simplify)
        intersect_areas_with_raster(areas, drop_constraints=True)
        for population in Population.objects.all():
            aggregate_population(area_level, population, drop_constraints=True)
        return Response({'message': f'{areas.count()} Areas pulled into database'},
                        status.HTTP_202_ACCEPTED)

    @extend_schema(description='Upload Geopackage/ZippedShapeFile with Areas',
                   request=inline_serializer(
                       name='PlaceFileDropConstraintSerializer',
                       fields={'file': serializers.FileField()}
                   ))
    @action(methods=['POST'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata],
            parser_classes=[CamelCaseMultiPartParser])
    def upload_shapefile(self, request, **kwargs):
        with ProtectedProcessManager(request.user):
            try:
                area_level: AreaLevel = self.queryset.get(**kwargs)
            except AreaLevel.DoesNotExist:
                msg = f'Area level for {kwargs} not found'
                return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)
            project_area = ProjectSetting.load().project_area
            if not project_area:
                msg = 'Project area is not defined'
                return Response({'message': msg}, status.HTTP_406_NOT_ACCEPTABLE)
            # ToDo: option to truncate or to update existing entries
            # when keys match
            # delete existing data
            Area.objects.filter(area_level=area_level).delete()
            AreaField.objects.filter(area_level=area_level).delete()
            geo_file = request.FILES['file']
            ext = '.'.join([''] + geo_file.name.split('.')[1:])
            if ext == '.zip':
                ext = '.shp.zip'
            mapping = {'geom': 'MULTIPOLYGON',}
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as fp:
                with open(fp.name, 'wb') as f:
                    f.write(geo_file.file.read())
                fp.close()
                try:
                    lm = CustomLayerMapping(Area,
                                            fp.name,
                                            mapping,
                                            custom={'area_level': area_level, })

                    layer = lm.layer
                    attributes = {}
                    for i, field_name in enumerate(layer.fields):
                        field_type = layer.field_types[i]
                        if issubclass(field_type, (gdal_field.OFTInteger,
                                                   gdal_field.OFTInteger64,
                                                   gdal_field.OFTReal)):
                            ft = FieldTypes.NUMBER
                        else:
                            ft = FieldTypes.STRING
                        try:
                            af = AreaField.objects.get(area_level=area_level,
                                                       name=field_name)
                        except AreaField.DoesNotExist:
                            try:
                                field_type = FieldType.objects.get(ftype=ft)
                            except FieldType.DoesNotExist:
                                field_type = FieldType.objects.create(ftype=ft,
                                                                      name=ft.value)
                            af = AreaField.objects.create(area_level=area_level,
                                                          name=field_name,
                                                          field_type=field_type)
                        attributes[field_name] = layer.get_fields(field_name)

                    lm.save(verbose=True, strict=True)
                except GDALException as e:
                    #msg = f'Upload failed: {e}'
                    msg = 'Die Datei konnte nicht gelesen werden. Bitte überprüfen '
                    'Sie, ob es sich um eine korrektes Shapefile bzw. Geopackage '
                    'handelt.'
                    return Response({'message': msg, },
                                    status=status.HTTP_406_NOT_ACCEPTABLE)

            areas = Area.objects.filter(area_level=area_level)
            for i, area in enumerate(areas):
                area_attrs = {field_name: attrs[i]
                              for field_name, attrs
                              in attributes.items()}
                area.attributes = area_attrs

                intersection = project_area.intersection(area.geom)
                if (intersection.area < MIN_AREA):
                    area.delete()
                    continue
                if intersection.area / area.geom.area < INTERSECT_THRESHOLD:
                    if isinstance(intersection, Polygon):
                        intersection = MultiPolygon(intersection)
                    area.geom = intersection
                    area.is_cut = True
                area.save()
            now = datetime.datetime.now()
            area_level.source.date = datetime.date(now.year, now.month, now.day)
            area_level.source.save()
            if areas:
                intersect_areas_with_raster(areas, drop_constraints=True)
                for population in Population.objects.all():
                    aggregate_population(area_level, population, drop_constraints=True)
            msg = f'Upload successful of {layer.num_feat} areas'
            return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)

    @action(methods=['POST'], detail=True,
            permission_classes=[HasAdminAccessOrReadOnly | CanEditBasedata])
    def clear(self, request, **kwargs):
        areas = Area.objects.filter(area_level=kwargs['pk'])
        count = areas.count()
        areas.delete()
        return Response({'message': f'{count} Areas deleted'},
                        status=status.HTTP_200_OK)


class AreaViewSet(ProtectCascadeMixin,
                  viewsets.ModelViewSet):

    serializer_class = AreaSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        """return the annotated queryset"""
        if self.detail:
            try:
                area_level = Area.objects.get(**self.kwargs).area_level_id
            except Area.DoesNotExist as e:
                raise Http404(str(e))
        else:
            area_level = self.request.query_params.get('area_level')
        if not area_level:
            raise BadRequest('No AreaLevel provided')
        areas = Area.label_annotated_qs(area_level)
        return areas

    @extend_schema(
        parameters=[OpenApiParameter(name='area_level', required=True, type=int)]
    )
    def list(self, request):
        return super().list(request)


class FieldTypeViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = FieldType.objects.all()
    serializer_class = FieldTypeSerializer
    permission_classes = [ProtectPresetPermission &
                          (HasAdminAccessOrReadOnly | CanEditBasedata)]


class AreaFieldViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = AreaField.objects.all()
    serializer_class = AreaFieldSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

