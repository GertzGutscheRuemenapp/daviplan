from test_plus import APITestCase

from datentool_backend.api_test import (BasicModelTest,
                                        WriteOnlyWithCanEditBaseDataTest,
                                        TestAPIMixin,
                                        TestPermissionsMixin,
                                        )
from datentool_backend.population.models import (PopStatistic,
                                                 PopStatEntry)
from datentool_backend.population.factories import (
    PopStatEntryFactory,
    PopStatisticFactory
)

from faker import Faker

faker = Faker('de-DE')


class TestPopStatisticAPI(WriteOnlyWithCanEditBaseDataTest,
                          TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "popstatistics"
    factory = PopStatisticFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        popstatistic: PopStatistic = cls.obj
        year = popstatistic.year.year

        cls.post_data = dict(year=year)
        cls.put_data = dict(year=year)
        cls.patch_data = dict(year=year)


class TestPopStatEntryAPI(WriteOnlyWithCanEditBaseDataTest,
                          TestPermissionsMixin, TestAPIMixin, BasicModelTest, APITestCase):
    """"""
    url_key = "popstatentries"
    factory = PopStatEntryFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        popstatentry: PopStatEntry = cls.obj
        popstatistic = popstatentry.popstatistic.pk
        area = popstatentry.area.pk

        data = dict(popstatistic=popstatistic, area=area,
                    immigration=faker.pyfloat(positive=True),
                    emigration=faker.pyfloat(positive=True),
                    births=faker.pyfloat(positive=True),
                    deaths=faker.pyfloat(positive=True))
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
