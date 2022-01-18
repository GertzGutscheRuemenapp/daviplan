from rest_framework_gis.fields import GeometryField
from django.contrib.gis.geos import MultiPolygon, Polygon


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
