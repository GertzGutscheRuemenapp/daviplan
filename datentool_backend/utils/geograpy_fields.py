from rest_framework_gis.fields import GeometryField
from django.contrib.gis.geos import MultiPolygon, Polygon


class MultiPolygonGeographyField(GeometryField):
    """A Geography Field that forces Multipolygon and WGS84"""

    def to_representation(self, value):
        """returns the field geometry EWKT"""
        return value.ewkt

    def to_internal_value(self, value):
        """Transform to Multipolygon, if its a Polygon and transform to WGS84"""
        internal = super().to_internal_value(value)
        if isinstance(internal, Polygon):
            internal = MultiPolygon(internal, srid=internal.srid)
        internal.transform(4326)
        return internal
