import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from django.test import TestCase
from django.conf import settings
from test_plus import APITestCase
from django.contrib.gis.geos import MultiPolygon

from datentool_backend.site.models import ProjectSetting

from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin,
                                        TestPermissionsMixin)

from faker import Faker

faker = Faker('de-DE')


from .factories import (ModeVariantFactory,
                        CutOffTimeFactory,
                        NetworkFactory
                        )
from .models import Network


class TestNetworkModels(TestCase):

    def test_mode_variant(self):
        mode_variant = ModeVariantFactory()

    def test_cut_off_time(self):
        cut_off_time = CutOffTimeFactory()

    def test_mode_default_unique(self):
        network_1 = NetworkFactory()
        network_2 = NetworkFactory()
        network_3 = NetworkFactory()

        network_3.is_default = True
        network_3.save()
        network_2.is_default = True
        network_2.save()

        self.assertEqual(Network.objects.get(is_default=True), network_2)

        network_2.is_default = False
        network_2.save()
        self.assertEqual(len(Network.objects.filter(is_default=True)), 0)


def copy_pbf_file(from_url, to_file, **kwargs):
    """mocks the download of data from geofabrik by copying small test data"""
    from_file = os.path.join(os.path.dirname(__file__),
                             'data',
                             'stockheim.osm.pbf')
    msg = 'Download completed'
    shutil.copyfile(from_file, to_file)
    return (to_file, msg)


class TestNetworkAPI(WriteOnlyWithCanEditBaseDataTest,
                     TestPermissionsMixin,
                     TestAPIMixin,
                     BasicModelTest,
                     APITestCase):
    """Test to post, put and patch data"""
    url_key = "networks"
    factory = NetworkFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        data = dict(name=faker.word(),
                    is_default=faker.pybool())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    @patch('datentool_backend.modes.views.urllib.request.urlretrieve')
    def test_pull_base_network(self, mock_urlretreive: Mock):
        """pull base network"""
        self.profile.admin_access = True
        self.profile.save()

        url = 'networks-pull-base-network'

        mock_urlretreive.side_effect = copy_pbf_file
        res = self.post(url)
        self.assert_http_202_accepted(res)

    def test_build_project_network_and_run(self):
        """pull a network"""
        self.profile.admin_access = True
        self.profile.save()

        url = 'networks-build-project-network'

        # without projectsettings it should fail
        res = self.post(url)
        self.assert_http_400_bad_request(
            res, 'Das Projektgebiet ist nicht definiert')

        # create project settings
        ewkt = 'SRID=4326;MULTIPOLYGON (((8.97 50.3, 9.02 50.3, 9.02 50.35, 8.97 50.35, 8.97 50.3)))'
        geom = MultiPolygon.from_ewkt(ewkt)
        geom.transform(3857)
        projectsettings = ProjectSetting.load()
        projectsettings.project_area = geom
        projectsettings.save()

        # delete base network from media-root if exists
        fp_base_pbf = os.path.join(settings.MEDIA_ROOT, 'germany-latest.osm.pbf')
        Path(fp_base_pbf).unlink(missing_ok=True)

        # without base network it should fail
        res = self.post(url)
        self.assert_http_400_bad_request(
            res, 'Das Basisnetz wurde noch nicht heruntergeladen')

        # copy the base network to the media-root-folder
        copy_pbf_file('', fp_base_pbf)

        # with projectsettings it should work
        res = self.post(url)
        self.assert_http_202_accepted(res)

        # run routers
        url = 'networks-run-routers'
        res = self.post(url)
        self.assert_http_200_ok(res, 'Routers running')
