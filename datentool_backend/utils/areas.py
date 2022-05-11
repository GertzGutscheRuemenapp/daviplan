import json
from requests import request
import datetime
from rest_framework.response import Response
from rest_framework import status
from owslib.wfs import WebFeatureService
from django.contrib.gis.geos import (GEOSGeometry, Polygon, MultiPolygon,
                                     GeometryCollection)

from datentool_backend.models import (AreaLevel,
                                      Area,
                                      SourceTypes,
                                      ProjectSetting
                                      )

# minimum area of feature in m² after intersection with project area
# otherwise ignored
MIN_AREA = 10000
# percentage of intersected area in relation to original geometry
# if above threshold uncut original geometry is taken
INTERSECT_THRESHOLD = 0.95

def pull_areas(area_level: AreaLevel, project_area,
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