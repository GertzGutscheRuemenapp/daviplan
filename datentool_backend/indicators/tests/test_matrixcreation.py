import os
from unittest import skipIf
import urllib
from typing import List
import logging
logger = logging.getLogger(name='test')

import pandas as pd
from test_plus import APITestCase
from django.conf import settings
from django.urls import reverse
from django.contrib.gis.geos import Point

from datentool_backend.utils.routers import OSRMRouter
from datentool_backend.api_test import LoginTestCase
from datentool_backend.indicators.tests.setup_testdata import CreateTestdataMixin
from datentool_backend.places.models import Place
from datentool_backend.places.factories import ScenarioFactory
from datentool_backend.indicators.models import (MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 )

from datentool_backend.modes.models import (Mode,
                                            Network,
                                            )
from datentool_backend.modes.factories import (ModeVariant,
                                               ModeVariantFactory,
                                               )


def no_connection(host: str = 'localhost',
                  port: int = 5000,
                  timeout: float = 1) -> bool:
    """
    try to access host:port with given timeout
    return True, if site is not answering (404, URLError)
    return False, if it is a BadRequest (400)
    """
    try:
        urllib.request.urlopen(f'http://{host}:{port}', timeout=timeout)
        return False
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return True
        return False
    except urllib.error.URLError as err:
        return True
    except Exception as err:
        return True


class TestMatrixCreation(CreateTestdataMixin,
                         LoginTestCase,
                         APITestCase):
    """Test to create a matrix"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.build_osrm()
        cls.profile.can_edit_basedata = True
        cls.profile.save()
        cls.create_project_settings()
        cls.create_years_gender_agegroups()
        cls.create_raster_population()
        infrastructure = cls.create_infrastructure_services()
        cls.create_places(infrastructure=infrastructure)
        cls.create_network()

    def test_create_airdistance_matrix(self):
        """Test to create an air distance matrix"""
        network = self.network
        walk = ModeVariantFactory(mode=Mode.WALK, network=network)
        car = ModeVariantFactory(mode=Mode.CAR, network=network)
        bike = ModeVariantFactory(mode=Mode.BIKE, network=network)

        data = {'variants': [walk.pk, car.pk, bike.pk],
                'drop_constraints': False,
                'air_distance_routing': True}

        res= self.post('matrixcellplaces-precalculate-traveltime', data=data,
                       extra={'format': 'json'})
        self.assert_http_202_accepted(res)
        logger.debug(res.content)
        logger.debug(MatrixCellPlace.objects.filter(variant=walk.pk).count())
        logger.debug(MatrixCellPlace.objects.filter(variant=car.pk).count())
        logger.debug(MatrixCellPlace.objects.filter(variant=bike.pk).count())

    def calc_cell_place_matrix(self,
                               variants: List[int],
                               access_variant:int=None,
                               places: List[int]=[],
                               air_distance_routing: bool=False,
                               max_distance: float = None) -> str:
        """
        calculate the matrix between cells and places
        and return the content of the response
        """
        data = {'variants': variants,
                'access_variant': access_variant,
                'drop_constraints': False,
                'places': places,
                'air_distance_routing': air_distance_routing,
                }
        if max_distance:
            data['max_distance'] = max_distance

        res = self.post('matrixcellplaces-precalculate-traveltime', data=data,
                        extra={'format': 'json'})
        self.assert_http_202_accepted(res)
        content = res.content
        return content

    @skipIf(not OSRMRouter(Mode.WALK).service_is_up, 'osrm docker not running')
    def test_create_routed_walk_matrix(self):
        """Test to create an walk matrix from routing"""
        network = self.network
        walk = ModeVariantFactory(mode=Mode.WALK, network=network)
        content = self.calc_cell_place_matrix(variants=[walk.pk])
        logger.debug(content)
        logger.debug(MatrixCellPlace.objects.filter(variant=walk.pk).count())

    @skipIf(not OSRMRouter(Mode.BIKE).service_is_up, 'osrm docker not running')
    def test_create_routed_bike_matrix(self):
        """Test to create an bicycle matrix from routing"""
        network = self.network
        bike = ModeVariantFactory(mode=Mode.BIKE, network=network)
        content = self.calc_cell_place_matrix(variants=[bike.pk])
        logger.debug(content)
        logger.debug(MatrixCellPlace.objects.filter(variant=bike.pk).count())
        url = 'matrixstatistics-list'
        response = self.get(url)
        self.assert_http_200_ok(response)
        data = response.data
        self.assertDictEqual(data['n_rels_place_cell_modevariant'],
                             {bike.pk: 40})

    @skipIf(not OSRMRouter(Mode.CAR).service_is_up, 'osrm docker not running')
    def test_create_routed_car_matrix(self):
        """Test to create an car matrix from routing"""
        network = self.network
        car = ModeVariantFactory(mode=Mode.CAR, network=network)
        content = self.calc_cell_place_matrix(variants=[car.pk])
        logger.debug(content)
        logger.debug(MatrixCellPlace.objects.filter(variant=car.pk).count())

    @skipIf(not OSRMRouter(Mode.CAR).service_is_up, 'osrm docker not running')
    def test_create_routed_car_matrix_with_multileveldijkstra(self):
        """Test to create an car matrix from routingmultilivel dijkstra"""
        network = self.network
        car = ModeVariantFactory(mode=Mode.CAR, network=network)

        original_algorithm = settings.ROUTING_ALGORITHM

        settings.ROUTING_ALGORITHM = 'mld'
        try:
            content = self.calc_cell_place_matrix(variants=[car.pk])
        finally:
            settings.ROUTING_ALGORITHM = original_algorithm
        logger.debug(content)
        logger.debug(MatrixCellPlace.objects.filter(variant=car.pk).count())



    @skipIf(not OSRMRouter(Mode.WALK).service_is_up or
            not OSRMRouter(Mode.BIKE).service_is_up or
            not OSRMRouter(Mode.CAR).service_is_up,
            'osrm docker not running')
    def test_create_routed_matrix_for_new_places(self):
        """Test to create an walk matrix from routing"""
        self.client.force_login(self.profile.user)
        # setup modevariants
        walk = ModeVariant.objects.get(mode=Mode.WALK, is_default=True)
        bike = ModeVariant.objects.get(mode=Mode.BIKE, is_default=True)
        car = ModeVariant.objects.get(mode=Mode.CAR, is_default=True)
        transit1 = ModeVariantFactory(mode=Mode.TRANSIT, network=None, label='T1')
        transit2 = ModeVariantFactory(mode=Mode.TRANSIT, network=None, label='T2')
        self.create_stops(transit_variant_id=transit1.pk)
        self.create_stops(transit_variant_id=transit2.pk)
        variants = [walk.pk, bike.pk, car.pk, transit1.pk, transit2.pk]

        # calculate initial number of relations
        content = self.calc_cell_place_matrix(variants=variants, access_variant=walk.pk)
        logger.debug(content)
        walk_rows_before = MatrixCellPlace.objects.filter(variant=walk.pk).count()
        self.assertEqual(walk_rows_before, 40)
        transit1_rows_before = MatrixCellPlace.objects.filter(variant=transit1.pk).count()
        self.assertEqual(transit1_rows_before, 40)
        transit2_rows_before = MatrixCellPlace.objects.filter(variant=transit2.pk).count()
        self.assertEqual(transit2_rows_before, 40)

        url = 'matrixstatistics-list'
        response = self.get(url)
        self.assert_http_200_ok(response)
        data = response.data
        self.assertDictEqual(data['n_rels_place_cell_modevariant'],
                             {walk.pk: 40,
                              bike.pk: 40,
                              car.pk: 40,
                              transit1.pk: 40,
                              transit2.pk: 40,
                              })
        self.assertDictEqual(data['n_rels_place_stop_modevariant'],
                             {transit1.pk: 3,
                              transit2.pk: 3,
                              })

        # add new places in a scenario
        scenario = ScenarioFactory()
        infrastructure = self.place1.infrastructure
        url = 'places-list'
        data = dict(name='NewPlace',
                    infrastructure=infrastructure.pk,
                    geom=Point(x=1000010, y=6500026, srid=3857).ewkt,
                    attributes={},
                    scenario=scenario.pk,
                    )
        res = self.post(url, data=data, extra={'format': 'json'})
        self.assert_http_201_created(res)
        new_place = Place.objects.get(pk=res.data['id'])

        # recalculate one place, add one new
        walk_rows_after = MatrixCellPlace.objects.filter(variant=walk.pk).count()
        self.assertEqual(walk_rows_after, 48)
        bike_to_new_place = MatrixCellPlace.objects.filter(variant=bike.pk,
                                                           place=new_place).count()
        self.assertEqual(bike_to_new_place, 8)
        transit1_rows_after = MatrixCellPlace.objects.filter(variant=transit1.pk).count()
        self.assertEqual(transit1_rows_after, 48)
        transit2_rows_after = MatrixCellPlace.objects.filter(variant=transit2.pk).count()
        self.assertEqual(transit2_rows_after, 48)

        url = 'matrixstatistics-list'
        response = self.get(url)
        self.assert_http_200_ok(response)
        data = response.data
        self.assertDictEqual(data['n_rels_place_cell_modevariant'],
                             {walk.pk: 48,
                              bike.pk: 48,
                              car.pk: 48,
                              transit1.pk: 48,
                              transit2.pk: 48,
                              })
        self.assertDictEqual(data['n_rels_place_stop_modevariant'],
                             {transit1.pk: 4,
                              transit2.pk: 4,
                              })

        url = 'places-detail'
        df_before = pd.DataFrame(
            MatrixCellPlace.objects.filter(place=self.place2).values())
        # change name of existing point
        patch_data = {'name': 'New Name', }
        res = self.patch(url, pk=self.place2.pk, data=patch_data, extra={'format': 'json'})
        self.assert_http_200_ok(res)
        self.place2.refresh_from_db()
        self.assertEqual(self.place2.name, patch_data['name'])
        df_after_patch_name = pd.DataFrame(
            MatrixCellPlace.objects.filter(place=self.place2).values())
        # changing name should not change the travel times
        pd.testing.assert_frame_equal(df_before, df_after_patch_name)

        # change geometry of existing point
        geom_before = self.place2.geom.ewkt

        x, y = 1000320, 6500036
        patch_data = {'geom': Point(x=x, y=y, srid=3857).ewkt, }
        res = self.patch(url, pk=self.place2.pk, data=patch_data, extra={'format': 'json'})
        self.assert_http_200_ok(res)
        self.place2.refresh_from_db()
        geom_after = self.place2.geom.ewkt
        # test if geometry changed
        self.assertAlmostEqual(self.place2.geom.x, x)
        self.assertAlmostEqual(self.place2.geom.y, y)

        df_after_patch_geom = pd.DataFrame(
            MatrixCellPlace.objects.filter(place=self.place2).values())

        # the travel times should have changed, if not, the exception would not be raised
        with self.assertRaises(AssertionError) as e:
            pd.testing.assert_frame_equal(df_after_patch_geom, df_before)

        places = [self.place2.pk, new_place.pk]
        content = self.calc_cell_place_matrix(variants=variants,
                                              access_variant=walk.pk,
                                              places=places,
                                              air_distance_routing=True)

        car_to_new_place = MatrixCellPlace.objects.filter(variant=car.pk,
                                                          place=new_place).count()
        self.assertEqual(car_to_new_place, 8)

        # delete new place
        new_place_id = new_place.pk
        self.assertTrue(MatrixCellPlace.objects.filter(place=new_place_id).exists())
        self.assertTrue(MatrixPlaceStop.objects.filter(place=new_place_id).exists())
        res = self.delete(url, pk=new_place_id, extra={'format': 'json',})
        self.assert_http_204_no_content(res)
        self.assertFalse(MatrixCellPlace.objects.filter(place=new_place_id).exists())
        self.assertFalse(MatrixPlaceStop.objects.filter(place=new_place_id).exists())

        url = 'matrixstatistics-list'
        response = self.get(url)
        self.assert_http_200_ok(response)
        data = response.data
        self.assertDictEqual(data['n_rels_place_cell_modevariant'],
                             {walk.pk: 40,
                              bike.pk: 40,
                              car.pk: 40,
                              transit1.pk: 40,
                              transit2.pk: 40,
                              })
        self.assertDictEqual(data['n_rels_place_stop_modevariant'],
                             {transit1.pk: 3,
                              transit2.pk: 3,
                              })

        # reset the geometry should reduce the number of PlaceStop to 12 again
        url = 'places-detail'
        patch_data = {'geom': geom_before}
        res = self.patch(url, pk=self.place2.pk, data=patch_data, extra={'format': 'json'})
        self.assert_http_200_ok(res)
        self.place2.refresh_from_db()
        url = 'matrixstatistics-list'
        response = self.get(url)
        self.assert_http_200_ok(response)
        data = response.data
        self.assertDictEqual(data['n_rels_place_cell_modevariant'],
                             {walk.pk: 40,
                              bike.pk: 40,
                              car.pk: 40,
                              transit1.pk: 40,
                              transit2.pk: 40,
                              })

    @classmethod
    def build_osrm(cls):
        pbf = os.path.join(os.path.dirname(__file__),
                           'testdata', 'projectarea.pbf')
        # ToDo: use own route to run and build to test
        for mode in [Mode.WALK, Mode.BIKE, Mode.CAR]:
            router = OSRMRouter(mode)
            if not router.service_is_up:
                return
            router.build(pbf)
            router.run()

    @classmethod
    def create_network(cls):
        """create network"""
        cls.network, created = Network.objects.get_or_create(is_default=True)

    def create_stops(self, transit_variant_id: int=None):
        """upload stops from excel-template"""

        if transit_variant_id:
            self.transit = ModeVariant.objects.get(id=transit_variant_id)
        else:
            self.transit, created = ModeVariant.objects.get_or_create(
                mode=Mode.TRANSIT, network=self.network)

       # upload stops
        file_path_transit = os.path.join(os.path.dirname(__file__),
                                    'testdata',
                                    'transit')
        file_path_stops = os.path.join(file_path_transit,
                                    'Haltestellen_Stockheim.xlsx')
        file_content = open(file_path_stops, 'rb')
        data = {
            'excel_file': file_content,
            'variant': self.transit.pk,
        }

        url = reverse('stops-upload-template')
        res = self.client.post(url, data, extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)

        #  upload traveltime-matrix from stop to stop
        file_path_matrix = os.path.join(file_path_transit,
                                 'Beförderungszeit.mtx')
        file_content = open(file_path_matrix, 'rb')
        data = {
            'excel_or_visum_file': file_content,
            'variant': self.transit.pk,
            'drop_constraints': False,
        }

        url = reverse('matrixstopstops-upload-template')
        res = self.client.post(url, data, extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)

    @skipIf(not OSRMRouter(Mode.WALK).service_is_up, 'osrm docker not running')
    def test_create_routed_cell_stop_walk_matrix(self):
        """Test to create an walk matrix from cell to stop"""
        self.create_stops()
        walk, created = ModeVariant.objects.get_or_create(mode=Mode.WALK,
                                                          network=self.network)
        content = self.calc_cell_stop_matrix(transit_variant=self.transit,
                                             access_variant=walk,
                                             max_distance=1000)
        logger.debug(content)
        logger.debug(MatrixCellStop.objects.filter(access_variant=walk.pk).count())

        content = self.calc_cell_stop_matrix(transit_variant=self.transit,
                                             access_variant=walk,
                                             max_distance=2000)
        logger.debug(content)
        logger.debug(MatrixCellStop.objects.filter(access_variant=walk.pk).count())

    def calc_cell_stop_matrix(self,
                              transit_variant: ModeVariant,
                              access_variant:ModeVariant,
                              max_distance: float=None) -> str:
        """
        calculate the matrix between cells and stops
        and return the content of the response
        """

        data = {'transit_variant': transit_variant.pk,
                'access_variant': access_variant.pk,
                'drop_constraints': False,
                }
        if max_distance:
            data['max_distance'] = max_distance

        res = self.post('matrixcellstops-precalculate-accesstime', data=data,
                        extra={'format': 'json'})
        self.assert_http_202_accepted(res)
        return res.content

    @skipIf(not OSRMRouter(Mode.WALK).service_is_up, 'osrm docker not running')
    def test_create_routed_place_stop_walk_matrix(self):
        """Test to create an walk matrix from place to stop"""
        self.create_stops()
        walk, created = ModeVariant.objects.get_or_create(mode=Mode.WALK,
                                                          network=self.network)

        content = self.calc_place_stop_matrix(transit_variant=self.transit,
                                              access_variant=walk)
        logger.debug(content)
        logger.debug(MatrixPlaceStop.objects.filter(access_variant=walk.pk).count())

    def calc_place_stop_matrix(self, transit_variant: ModeVariant,
                               access_variant: ModeVariant,
                               max_distance: float = None) -> str:
        """
        calculate the matrix between cells and stops
        and return the content of the response
        """
        data = {'transit_variant': transit_variant.pk,
                'access_variant': access_variant.pk,
                'drop_constraints': False,
                }
        if max_distance:
            data['max_distance'] = max_distance

        res = self.post('matrixplacestops-precalculate-accesstime', data=data,
                        extra={'format': 'json'})
        self.assert_http_202_accepted(res)
        return res.content

    @skipIf(not OSRMRouter(Mode.WALK).service_is_up, 'osrm docker not running')
    def test_create_place_cell_transit_matrix(self):
        """Test to create an transit matrix from place to stop"""
        self.create_stops()
        walk, created = ModeVariant.objects.get_or_create(mode=Mode.WALK,
                                                          network=self.network)
        # precalculate the walk time from places and rastercells to stops
        content = self.calc_cell_stop_matrix(transit_variant=self.transit,
                                             access_variant=walk,
                                             max_distance=1000)
        content = self.calc_place_stop_matrix(transit_variant=self.transit,
                                              access_variant=walk,
                                              max_distance=1500)
        # until 800 m walk the way, if it's faster, over 800 m always take transit
        # ToDo: add max_distance
        content = self.calc_cell_place_matrix(variants=[walk.pk],
                                              max_distance=800)


        data = {'variants': [self.transit.pk],
                'drop_constraints': False,
                'access_variant': walk.pk,
                }

        #  use default access distance to stops
        res = self.post('matrixcellplaces-precalculate-traveltime', data=data,
                        extra={'format': 'json'})
        self.assert_http_202_accepted(res)
        logger.debug(res.content)
        logger.debug(MatrixCellPlace.objects.filter(variant=self.transit.pk).count())
        #  try longer access distance to stops
        data['max_access_distance'] = 2000
        res = self.post('matrixcellplaces-precalculate-traveltime', data=data,
                        extra={'format': 'json'})
        self.assert_http_202_accepted(res)
        logger.debug(res.content)
        logger.debug(MatrixCellPlace.objects.filter(variant=self.transit.pk).count())

        url = 'matrixstatistics-list'
        response = self.get(url)
        self.assert_http_200_ok(response)
        data = response.data
        self.assertDictEqual(data['n_rels_place_cell_modevariant'],
                             {walk.pk: 36,
                              self.transit.pk: 40,})

        self.assertEqual(data['n_stops'], {self.transit.pk: 383})
        self.assertDictEqual(data['n_rels_place_stop_modevariant'],
                             {self.transit.pk: 27, })
        self.assertDictEqual(data['n_rels_stop_cell_modevariant'],
                             {self.transit.pk: 34, })
        self.assertDictEqual(data['n_rels_stop_stop_modevariant'],
                             {self.transit.pk: 88412, })
