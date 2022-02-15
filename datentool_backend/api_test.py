from django.http import HttpRequest
from collections import OrderedDict

from rest_framework_gis.fields import GeoJsonDict
from django.utils.encoding import force_str
from rest_framework import status
from django.db.models.query import QuerySet
from datentool_backend.utils.geometry_fields import compare_geometries, NoWKTError

from datentool_backend.user.factories import ProfileFactory, Profile
from django.contrib.auth.models import Permission
from datentool_backend.rest_urls import urlpatterns


class CompareAbsURIMixin:
    """
    Mixin thats provide a method
    to compare lists of relative with absolute url
    """
    @property
    def build_absolute_uri(self):
        """return the absolute_uri-method"""
        request = HttpRequest()
        request.META = self.client._base_environ()
        return request.build_absolute_uri

    def assertURLEqual(self, url1, url2, msg=None):
        """Assert that two urls are equal, if they were absolute urls"""
        absurl1 = self.build_absolute_uri(url1)
        absurl2 = self.build_absolute_uri(url2)
        self.assertEqual(absurl1, absurl2, msg)

    def assertURLsEqual(self, urllist1, urllist2, msg=None):
        """
        Assert that two lists of urls are equal, if they were absolute urls
        the order does not matter
        """
        absurlset1 = {self.build_absolute_uri(url) for url in urllist1}
        absurlset2 = {self.build_absolute_uri(url) for url in urllist2}
        self.assertSetEqual(absurlset1, absurlset2, msg)


class LoginTestCase:

    user = 99
    permissions = Permission.objects.all()
    profile: Profile

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile = ProfileFactory(id=cls.user,
                                    user__id=cls.user,
                                    user__username='Anonymus User',
                                    can_create_process=False,
                                    admin_access=False,
                                    can_edit_basedata=False)

    def setUp(self):
        self.client.force_login(user=self.profile.user)
        super().setUp()

    def tearDown(self):
        self.client.logout()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        user = cls.profile.user
        user.delete()
        cls.profile.delete()
        del cls.profile
        super().tearDownClass()


class BasicModelCompareMixin:
    baseurl = 'http://testserver'
    url_key = ""
    sub_urls = []
    url_pks = dict()
    url_pk = dict()
    query_params = dict()
    do_not_check = []

    def assert_response_equals_expected(self, response_value, expected):
        """
        Assert that response_value equals expected
        If response_value is a GeoJson, then compare the texts
        """
        if isinstance(response_value, GeoJsonDict):
            self.assertJSONEqual(force_str(response_value), expected)
        elif isinstance(response_value, (list, QuerySet)):
            self.assertEqual(len(response_value), len(expected))
            for i, response_elem in enumerate(response_value):
                expected_elem=expected[i]
                if isinstance(response_elem, dict):
                    self.assertDictContainsSubset(expected_elem, response_elem)
                else:
                    self.assertEqual(force_str(response_value), force_str(expected))
        elif isinstance(expected, (dict, OrderedDict)):
            self.assertDictContainsSubset(response_value, expected)
            self.assertDictContainsSubset(expected, response_value)
        else:
            try:
                compare_geometries(response_value, expected, tolerance=0.1)
            except NoWKTError:
                self.assertEqual(force_str(response_value), force_str(expected))

    def compare_data(self, left, right):
        """
        recursive comparison of two data dictionaries (response and expectation)
        """
        left = dict(left)
        for key in left:
            if key not in right or key in self.do_not_check:
                continue
            if isinstance(left[key], dict):
                # recursive check if nested
                self.compare_data(left[key], right[key])
            else:
                self.assert_response_equals_expected(left[key], right[key])

    def get_check_200(self, url, **kwargs):
        assert url in [r.name for r in urlpatterns], f'URL {url} not in routes'
        response = self.get(url, **kwargs)
        self.response_200(response, msg=response.content)
        return response


class BasicModelDetailTest(BasicModelCompareMixin, LoginTestCase, CompareAbsURIMixin):

    @property
    def kwargs(self):
        kwargs = {**self.url_pks, 'pk': self.obj.pk}
        if self.query_params:
            kwargs['data'] = self.query_params
        return kwargs

    def test_detail(self):
        self._test_detail()

    def _test_detail_forbidden(self):
        """Test get, put, patch methods for the detail-view"""
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        # test get
        response = self.get(url, **kwargs)
        self.response_403(msg=response.content)

    def _test_detail(self):
        """Test get, put, patch methods for the detail-view"""
        url = self.url_key + '-detail'

        # test get
        response = self.get_check_200(url, **self.kwargs)
        assert response.data['id'] == self.obj.pk



class SingletonRoute:
    """"""
    @property
    def kwargs(self):
        return {**self.url_pks}

    def test_detail(self):
        """Test get, put, patch methods for the detail-view"""
        url = self.url_key + '-detail'

        # test get
        response = self.get_check_200(url, **self.kwargs)


class BasicModelListMixin:

    @property
    def kwargs_list(self):
        kwargs = {**self.url_pks}
        if self.query_params:
            kwargs['data'] = self.query_params
        return kwargs

    def test_list(self):
        self._test_list()

    def _test_list_forbidden(self):
        """Test that the list view can not be returned successfully"""
        url = self.url_key + '-list'
        # test get
        response = self.get(url, **self.kwargs_list)
        self.response_403(msg=response.content)

    def _test_list(self):
        """Test that the list view can be returned successfully"""
        response = self.get(self.url_key + '-list', **self.kwargs_list)
        self.response_200(response, msg=response.content)




class BasicModelListTest(BasicModelCompareMixin, BasicModelListMixin,
                         LoginTestCase, CompareAbsURIMixin):
    """"""


class BasicModelReadTest(BasicModelListMixin, BasicModelDetailTest):

    def test_get_urls(self):
        self._test_get_urls()

    def _test_get_urls_forbidden(self):
        """get all sub-elements of a list of urls"""
        url = self.url_key + '-detail'
        # test get
        response = self.get(url, **self.kwargs)
        self.response_403(msg=response.content)

    def _test_get_urls(self):
        """get all sub-elements of a list of urls"""
        url = self.url_key + '-detail'
        response = self.get_check_200(url, **self.kwargs)
        for key in self.sub_urls:
            key_response = self.get_check_200(response.data[key])


class BasicModelPutPatchTest:
    """Test Put and Patch"""
    put_data = dict()
    patch_data = dict()
    expected_put_data = dict()
    expected_patch_data = dict()

    def test_put_patch(self):
        self._test_put_patch()

    def _test_put_patch_forbidden(self):
        """Test that put, patch methods are forbidden and return 403"""
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        formatjson = dict(format='json')
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=formatjson)
        self.response_403(msg=response.content)
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_403(msg=response.content)

    def _test_put_patch(self):
        """Test get, put, patch methods for the detail-view"""
        url = self.url_key + '-detail'
        kwargs = self.kwargs
        formatjson = dict(format='json')

        # test get
        response = self.get_check_200(url, **kwargs)
        if 'id' in response.data:
            assert response.data['id'] == self.obj.pk

        # check status code for put
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=formatjson)
        self.response_200(msg=response.content)
        assert response.status_code == status.HTTP_200_OK
        # check if values have changed
        response = self.get_check_200(url, **kwargs)

        expected = self.put_data.copy()
        expected.update(self.expected_put_data)
        self.compare_data(response.data, expected)

        # check status code for patch
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_200(msg=response.content)

        # check if name has changed
        response = self.get_check_200(url, **kwargs)

        expected = self.patch_data.copy()
        expected.update(self.expected_patch_data)
        self.compare_data(response.data, expected)


class BasicModelPostDeleteTest:
    post_urls = []
    post_data = dict()
    expected_post_data = dict()

    def test_delete(self):
        self._test_delete()

    def _test_delete(self):
        """Test delete method for the detail-view"""
        kwargs = self.kwargs
        url = self.url_key + '-detail'
        response = self.get_check_200(url, **kwargs)
        data = response.data

        response = self.delete(url, **kwargs)
        self.response_204(msg=response.content)

        # it should be deleted and raise 404
        response = self.get(url, **kwargs)
        self.response_404(msg=response.content)

    def _test_delete_forbidden(self):
        """Test that delete is forbidden"""
        kwargs = self.kwargs
        url = self.url_key + '-detail'
        response = self.delete(url, **kwargs)
        self.response_403(msg=response.content)

    def test_post(self):
        self._test_post()

    def _test_post(self):
        """Test post method for the detail-view"""
        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_201(msg=response.content)

        expected = self.post_data.copy()
        expected.update(self.expected_post_data)
        self.compare_data(response.data, expected)

        # get the created object
        new_id = response.data['id']
        url = self.url_key + '-detail'
        self.get_check_200(url, pk=new_id, **self.url_pks)

    def _test_post_forbidden(self):
        """Test that if post is forbidden, 403 is returned"""
        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_403(msg=response.content)

    def test_post_url_exist(self):
        self._test_post_url_exist()

    def _test_post_url_exist(self):
        """post all sub-elements of a list of urls"""
        url = self.url_key + '-detail'
        response = self.get_check_200(url, pk=self.obj.pk, **self.url_pks)
        for url in self.post_urls:
            response = self.get_check_200(url)


class BasicModelTest(BasicModelPutPatchTest,
                     BasicModelPostDeleteTest,
                     BasicModelReadTest):
    """Tests all REST Methods"""


class BasicModelSingletonTest(SingletonRoute,
                              BasicModelPutPatchTest,
                              BasicModelDetailTest):
    """Tests Get-Detail, Put and Patch Methods"""


class BasicModelReadPermissionTest(BasicModelReadTest):
    def test_list_permission(self):
        self.profile.user.user_permissions.clear()
        response = self.get(self.url_key + '-list', **self.url_pks)
        self.response_403(msg=response.content)

    def test_get_permission(self):
        self.profile.user.user_permissions.clear()
        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': self.obj.pk, }
        response = self.get(url, **kwargs)
        self.response_403(msg=response.content)


class BasicModelWritePermissionTest(BasicModelTest):

    def test_post_permission(self):
        """
        Test if user can post without permission
        """
        self.profile.user.user_permissions.clear()
        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_403(msg=response.content)

    def test_delete_permission(self):
        """
        Test if user can delete without permission
        """
        self.profile.user.user_permissions.clear()
        kwargs = {**self.url_pks, 'pk': self.obj.pk, }
        url = self.url_key + '-detail'
        response = self.delete(url, **kwargs)
        self.response_403(msg=response.content)

    def test_put_permission(self):
        self.profile.user.user_permissions.clear()
        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': self.obj.pk, }
        formatjson = dict(format='json')
        response = self.put(url, **kwargs, data=self.put_data,
                            extra=formatjson)
        self.response_403(msg=response.content)


class BasicModelPermissionTest(BasicModelReadPermissionTest,
                               BasicModelWritePermissionTest):
    """
    Test of read and write permissions
    """


class WriteOnlyWithCanEditBaseDataTest:

    def test_delete(self):
        """Test delete with and without can_edit_basedata permissions"""
        self.profile.can_edit_basedata = True
        self.profile.save()
        self._test_delete()
        self.profile.can_edit_basedata = False
        self.profile.save()
        self._test_delete_forbidden()

    def test_post(self):
        """Test post with and without can_edit_basedata permissions"""
        self.profile.can_edit_basedata = True
        self.profile.save()
        self._test_post()
        self.profile.can_edit_basedata = False
        self.profile.save()
        self._test_post_forbidden()

    def test_put_patch(self):
        """Test post with and without can_edit_basedata permissions"""
        self.profile.can_edit_basedata = True
        self.profile.save()
        self._test_put_patch()
        self.profile.can_edit_basedata = False
        self.profile.save()
        self._test_put_patch_forbidden()

    def test_is_logged_in(self):
        """Test read, if user is authenticated"""
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)

        self.test_list()
        self.test_detail()


class WriteOnlyWithAdminAccessTest:

    def test_delete(self):
        """Test delete with and without can_edit_basedata permissions"""
        self.profile.admin_access = True
        self.profile.save()
        self._test_delete()
        self.profile.admin_access = False
        self.profile.save()
        self._test_delete_forbidden()

    def test_post(self):
        """Test post with and without can_edit_basedata permissions"""
        self.profile.admin_access = True
        self.profile.save()
        self._test_post()
        self.profile.admin_access = False
        self.profile.save()
        self._test_post_forbidden()

    def test_put_patch(self):
        """Test post with and without can_edit_basedata permissions"""
        self.profile.admin_access = True
        self.profile.save()
        self._test_put_patch()
        self.profile.admin_access = False
        self.profile.save()
        self._test_put_patch_forbidden()

    def test_is_logged_in(self):
        """Test read, if user is authenticated"""
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)

        self.test_list()
        self.test_detail()


class ReadOnlyWithAdminBasedataAccessTest:

    def test_detail(self):
        """Test detail with and without can_edit_basedata permissions or admin_access"""
        self.profile.admin_access = True
        self.profile.save()
        self._test_detail()
        self.profile.admin_access = False
        self.profile.save()
        self._test_detail_forbidden()

        self.profile.can_edit_basedata = True
        self.profile.save()
        self._test_detail()
        self.profile.can_edit_basedata = False
        self.profile.save()
        self._test_detail_forbidden()

    def test_get_urls(self):
        """Test get_urls with and without can_edit_basedata permissions"""
        self.profile.admin_access = True
        self.profile.save()
        self._test_get_urls()
        self.profile.admin_access = False
        self.profile.save()
        self._test_get_urls_forbidden()

        self.profile.can_edit_basedata = True
        self.profile.save()
        self._test_get_urls()
        self.profile.can_edit_basedata = False
        self.profile.save()
        self._test_get_urls_forbidden()

    def test_list(self):
        """Test list with and without can_edit_basedata permissions"""
        self.profile.admin_access = True
        self.profile.save()
        self._test_list()
        self.profile.admin_access = False
        self.profile.save()
        self._test_list_forbidden()

        self.profile.can_edit_basedata = True
        self.profile.save()
        self._test_list()
        self.profile.can_edit_basedata = False
        self.profile.save()
        self._test_list_forbidden()

    def test_is_logged_in(self):
        """Test get, if user is authenticated"""
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        # test_list() with check of admin_access
        self.profile.admin_access = True
        self.profile.save()
        self._test_list()
        self.profile.admin_access = False
        self.profile.save()
        self._test_list_forbidden()

        # test_detail()
        self.profile.admin_access = True
        self.profile.save()
        self._test_detail()
        self.profile.admin_access = False
        self.profile.save()
        self._test_detail_forbidden()


class SingletonWriteOnlyWithCanEditBaseDataTest:

    def test_put_patch(self):
        """Test for Singletons, put and patch with and without can_edit_basedata permissions"""
        self.profile.can_edit_basedata = True
        self.profile.save()
        self._test_put_patch()
        self.profile.can_edit_basedata = False
        self.profile.save()
        self._test_put_patch_forbidden()

    def test_is_logged_in(self):
        """Test read, if user is authenticated"""
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)

        self.test_detail()


class SingletonWriteOnlyWithAdminAccessTest:

    def test_put_patch(self):
        """Test for Singletons, put and patch with and without admin_access"""
        self.profile.admin_access= True
        self.profile.save()
        self._test_put_patch()
        self.profile.admin_access= False
        self.profile.save()
        self._test_put_patch_forbidden()

    def test_is_logged_in(self):
        """Test read, if user is authenticated"""
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)

        self.test_detail()


class TestAPIMixin:
    """test if view and serializer are working correctly """
    url_key = ""
    # replace with concrete factory in sub-class
    factory = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url_pks = dict()
        if cls.factory:
            cls.obj = cls.factory()
            cls.url_pk = dict(pk=cls.obj.pk)


class TestPermissionsMixin():
    """ test users permissions"""
    def test_is_logged_in(self):
        self.client.logout()
        response = self.get(self.url_key + '-list')
        self.response_302 or self.assert_http_401_unauthorized(response, msg=response.content)

        self.client.force_login(user=self.profile.user)
        self.test_list()
        self.test_detail()

    def test_can_edit_basedata(self):
        profile = self.profile

        original_permission = profile.can_edit_basedata
        original_admin_access = profile.admin_access

        # Testprofile, with permission to edit basedata
        profile.can_edit_basedata = True
        profile.admin_access = False
        profile.save()
        self.test_post()

        # Testprofile, without permission to edit basedata
        profile.can_edit_basedata = False
        profile.save()

        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                                 extra={'format': 'json'})
        self.response_403(msg=response.content)

        profile.can_edit_basedata = original_permission
        profile.admin_access = original_admin_access
        profile.save()

    def admin_access(self):
        profile = self.profile

        original_permission = profile.admin_access

        # Testprofile, with admin_acces
        profile.admin_access = True
        profile.save()
        self.test_post()

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

