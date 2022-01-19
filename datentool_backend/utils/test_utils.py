from unittest import TestCase

from datentool_backend.utils.geometry_fields import NoWKTError, compare_geometries
from django.contrib.gis.geos import (GEOSGeometry,
                                     Point, MultiPoint,
                                     LineString, MultiLineString,
                                     Polygon, MultiPolygon)


class TestGeometryCompare(TestCase):

    def test_no_wkt(self):
        wkt1 = 'NoWkt'
        wkt2 = 123
        with self.assertRaises(NoWKTError):
            compare_geometries(wkt1, wkt2, tolerance=0.01)

    def test_wkt_equal(self):
        pnt = Point(x=3, y=4, z=5, srid=4326)
        compare_geometries(pnt.ewkt, pnt.ewkt, 0)

    def test_pnt_closeby(self):
        pnt1 = Point(x=3, y=4, z=5, srid=4326)
        pnt2 = Point(x=4, y=4, z=5, srid=4326)
        pnt3 = Point(x=3.0001, y=4, z=5, srid=4326)
        pnt4 = Point(x=4, y=3, z=5, srid=4326)
        pnt5 = Point(x=3, y=3, z=5, srid=4326)

        # different geometrytypes
        with self.assertRaises(AssertionError):
            compare_geometries(pnt1.ewkt,
                               MultiPoint((pnt1, )).ewkt, 0)

        # points too far away
        with self.assertRaises(AssertionError):
            compare_geometries(pnt1.ewkt, pnt2.ewkt, 0.01)
        with self.assertRaises(AssertionError):
            compare_geometries(pnt1.ewkt, pnt3.ewkt, 0.0001)
        # points close enough for the tolerance
        compare_geometries(pnt1.ewkt, pnt3.ewkt, 0.01)

        # points close enough for the tolerance
        compare_geometries(MultiPoint((pnt1, pnt3)).ewkt,
                           MultiPoint((pnt1, pnt1)).ewkt, 0.01)
        # multipoints too far away
        with self.assertRaises(AssertionError):
            compare_geometries(MultiPoint((pnt1, pnt3)).ewkt,
                               MultiPoint((pnt1, pnt1)).ewkt, 0.0001)

        # length of linestrings in tolerance
        compare_geometries(LineString((pnt2, pnt3)).ewkt,
                           LineString((pnt2, pnt1)).ewkt, 0.01)
        # length of linestrings beyond tolerance
        with self.assertRaises(AssertionError):
            compare_geometries(LineString((pnt2, pnt3)).ewkt,
                               LineString((pnt2, pnt1)).ewkt, 0.0001)

        # Area of polygons in tolerance
        compare_geometries(Polygon((pnt1, pnt2, pnt4, pnt5, pnt1)).ewkt,
                           Polygon((pnt3, pnt2, pnt4, pnt5, pnt3)).ewkt, 0.01)
        # Area of polygons beyond tolerance
        with self.assertRaises(AssertionError):
            compare_geometries(Polygon((pnt1, pnt2, pnt4, pnt5, pnt1)).ewkt,
                               Polygon((pnt3, pnt2, pnt4, pnt5, pnt3)).ewkt, 0.000001)
