from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelReadTest,
                                        BasicModelPutPatchTest,
                                        ReadOnlyWithAdminBasedataAccessTest)
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
    def test_basedata_read_only(self):
        profile = self.profile

        original_basedata = profile.can_edit_basedata
        original_admin_access = profile.admin_access

        # Testprofile, with permission to edit basedata, without admin_acces
        profile.can_edit_basedata = True
        profile.admin_access = False
        profile.save()

        # test post
        url = self.url_key + '-list'
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        # test get, put, patch:
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        formatjson = dict(format='json')

        # test get
        response = self.get_check_200(url, **kwargs)
        if 'id' in response.data:
            assert response.data['id'] == self.obj.pk

        # test put
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=formatjson)
        self.response_403(msg=response.content)

        # check status code for patch
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_403(msg=response.content)


        # Testprofile, without permission to edit basedata
        profile.can_edit_basedata = False
        profile.save()

        # test post
        url = self.url_key + '-list'
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        # test get, put, patch
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        formatjson = dict(format='json')

        # test get
        response = self.get(url, **kwargs)
        self.response_403(msg=response.content)

        # test put
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=formatjson)
        self.response_403(msg=response.content)

        # check status code for patch
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_403(msg=response.content)

        profile.can_edit_basedata = original_basedata
        profile.admin_access = original_admin_access
        profile.save()

    def test_admin_read_only(self):
        profile = self.profile

        original_basedata = profile.can_edit_basedata
        original_admin_access = profile.admin_access
        profile.save()

        # Testprofile, with admin_acces, without can_edit_basedata
        profile.can_edit_basedata = False
        profile.admin_access = True
        profile.save()

        # test post
        url = self.url_key + '-list'
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        # test get, put, patch:
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        formatjson = dict(format='json')

        # test get
        response = self.get_check_200(url, **kwargs)
        if 'id' in response.data:
            assert response.data['id'] == self.obj.pk

        # test put
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=formatjson)
        self.response_403(msg=response.content)

        # check status code for patch
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_403(msg=response.content)

        # Testprofile, without admin_acces
        profile.admin_access = False
        profile.save()

        # test post
        url = self.url_key + '-list'
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        # test get, put, patch
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        formatjson = dict(format='json')

        # test get
        response = self.get(url, **kwargs)
        self.response_403(msg=response.content)
        # test put
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=formatjson)
        self.response_403(msg=response.content)

        # check status code for patch
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_403(msg=response.content)

        profile.can_edit_basedata = original_basedata
        profile.admin_access = original_admin_access
        profile.save()

    def test_is_logged_in(self):
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)

        self.test_list()
        self.test_detail()


class TestCapacityUploadLogAPI(ReadOnlyWithAdminBasedataAccessTest,
                               _TestReadOnly, _TestAPI, BasicModelReadTest, APITestCase):
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


class TestPlaceUploadLogAPI(ReadOnlyWithAdminBasedataAccessTest, _TestReadOnly, _TestAPI, BasicModelReadTest, APITestCase):
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


class TestAreaUploadLogAPI(ReadOnlyWithAdminBasedataAccessTest, _TestReadOnly, _TestAPI, BasicModelReadTest, APITestCase):
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
