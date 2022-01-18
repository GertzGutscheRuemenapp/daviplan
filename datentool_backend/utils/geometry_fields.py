import sys
from rest_framework_gis.fields import GeometryField
from django.utils.encoding import force_str

from django.contrib.gis.geos import (GEOSGeometry,
                                     Point, MultiPoint,
                                     LineString, MultiLineString,
                                     Polygon, MultiPolygon)

class MultiPolygonGeometrySRIDField(GeometryField):
    """A Geometry-Field that forces Multipolygon and the given srid"""

    def __init__(self, srid: int=3857, *args, **kwargs):
        self.srid = srid
        return super().__init__(*args, **kwargs)

    def to_representation(self, value) -> str:
        """returns the field geometry EWKT"""
        return value.ewkt

    def to_internal_value(self, value):
        """Transform to Multipolygon, if its a Polygon and transform to the given srid"""
        internal = super().to_internal_value(value)
        if isinstance(internal, Polygon):
            internal = MultiPolygon(internal, srid=internal.srid)
        internal.transform(self.srid)
        return internal


class GeometrySRIDField(GeometryField):
    """A Geometry-Field that converts to the given srid"""

    def __init__(self, srid: int=3857, *args, **kwargs):
        self.srid = srid
        return super().__init__(*args, **kwargs)

    def to_representation(self, value) -> str:
        """returns the field geometry EWKT"""
        return value.ewkt

    def to_internal_value(self, value):
        """Transform to the given srid"""
        internal = super().to_internal_value(value)
        internal.transform(self.srid)
        return internal


class NoWKTError(ValueError):
    """string is not valid (e)wkt and cannot be converted to geometry"""

def compare_geometries(wkt1: str, wkt2: str, tolerance: float):
    """
    compare if two strings are (e)wkt (raise ValueError otherwise)
    and if yes if they are more or less equal
    """
    # check first if the wkt are identical
    if force_str(wkt1) == force_str(wkt2):
        return

    # otherwise try to convert them to geometries
    try:
        geom1 = GEOSGeometry(wkt1)
        geom2 = GEOSGeometry(wkt2)
    except (ValueError, TypeError) as err:
        #  no valid geometries
        raise NoWKTError()

    assert isinstance(geom1, type(geom2)), 'GeometryTypes do not match'
    assert geom1.srid == geom2.srid, 'SRID does not match'
    assert geom1.num_coords == geom2.num_coords, 'Number of coordinates different'

    if isinstance(geom1, (Point, )):
        assert geom1.distance(geom2) < tolerance, 'Distance of the point too big'
    elif isinstance(geom1, (MultiPoint, )):
        for i, pnt in enumerate(geom1):
            assert pnt.distance(geom2[i]) < tolerance, 'Distance of the points too big'
    elif isinstance(geom1, (LineString, MultiLineString)):
        assert geom1.length - geom1.length < tolerance, 'Length of the Linestring do not match'
    elif isinstance(geom1, (Polygon, MultiPolygon)):
        assert geom1.sym_difference(geom2).area < tolerance, 'Area of the symmetric difference of the areas too big'


