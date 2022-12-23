from test_plus import APITestCase

from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin, TestPermissionsMixin)


from datentool_backend.indicators.factories import RouterFactory


from faker import Faker
faker = Faker('de-DE')


class TestRouterAPI(WriteOnlyWithCanEditBaseDataTest,
                    TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "routers"
    factory = RouterFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        data = dict(name = faker.word(),
                    osm_file = faker.file_path(),
                    tiff_file = faker.file_path(),
                    gtfs_file = faker.file_path(),
                    build_date = faker.date(),
                    buffer = faker.random_number(digits=2))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

