from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelReadTest
from datentool_backend.area.tests import _TestAPI

from .factories import (CapacityUploadLogFactory, PlaceUploadLogFactory,
                        AreaUploadLogFactory)

from ..user.factories import ProfileFactory

from .models import (CapacityUploadLog, PlaceUploadLog, AreaUploadLog)

from faker import Faker

faker = Faker('de-DE')


class TestLogs(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.profile = ProfileFactory()

    def test_capacity_log(self):
        log = CapacityUploadLogFactory(user=self.profile)

    def test_indicator(self):
        log = PlaceUploadLogFactory(user=self.profile)

    def test_matrix(self):
        log = AreaUploadLogFactory()


class _TestReadOnly():
    """Test if user can read_only if attributes can_edit_basedata or has_admin_access are true"""
    def read_only_basedata(self):
        profile = self.profile

        original_permission = profile.can_edit_basedata

        # Testprofile, with permission to edit basedata
        profile.can_edit_basedata = True
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        # Testprofile, without permission to edit basedata
        profile.can_edit_basedata = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.can_edit_basedata = original_permission
        profile.save()

    def read_only_admin_access(self):
        profile = self.profile

        original_permission = profile.admin_access

        # Testprofile, with admin_acces
        profile.admin_access = True
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        # Testprofile, without admin_acces
        profile.admin_access = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.admin_access = original_permission
        profile.save()


class TestCapacityUploadLogAPI(_TestReadOnly, _TestAPI, BasicModelReadTest, APITestCase):
    """"""
    url_key = "capacityuploadlogs"
    factory = CapacityUploadLogFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        capacityuploadlog: CapacityUploadLog = cls.obj
        service = capacityuploadlog.service.pk
        user = capacityuploadlog.user.pk

        data = dict(user=user, date = faker.date(), text = faker.sentence(),
                    service=service)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_read_only_basedata(self):
        super().read_only_basedata()

    def test_read_only_admin_access(self):
        super().read_only_admin_access()



class TestPlaceUploadLogAPI(_TestReadOnly, _TestAPI, BasicModelReadTest, APITestCase):
    """"""
    url_key = "placeuploadlogs"
    factory = PlaceUploadLogFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        placeuploadlog: PlaceUploadLog = cls.obj
        infrastructure = placeuploadlog.infrastructure.pk
        user = placeuploadlog.user.pk

        data = dict(user=user, date = faker.date(), text = faker.sentence(),
                    infrastructure=infrastructure)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_read_only_basedata(self):
        super().read_only_basedata()

    def test_read_only_admin_access(self):
        super().read_only_admin_access()


class TestAreaUploadLogAPI(_TestReadOnly, _TestAPI, BasicModelReadTest, APITestCase):
    """"""
    url_key = "areauploadlogs"
    factory = AreaUploadLogFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        areauploadlog: AreaUploadLog = cls.obj
        level = areauploadlog.level.pk
        user = areauploadlog.user.pk

        data = dict(user=user, date = faker.date(), text = faker.sentence(),
                    level=level)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_read_only_basedata(self):
        super().read_only_basedata()

    def test_read_only_admin_access(self):
        super().read_only_admin_access()
