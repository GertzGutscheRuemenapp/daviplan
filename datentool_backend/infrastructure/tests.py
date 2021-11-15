from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI
from ..user.factories import ProfileFactory

from .factories import (InfrastructureFactory, ServiceFactory, CapacityFactory,
                        FClassFactory, PlaceFieldFactory)
from .models import Infrastructure


from faker import Faker

faker = Faker('de-DE')


class TestInfrastructure(TestCase):

    def test_service(self):
        service = ServiceFactory()
        print(service.quota)

    def test_infrastructure(self):
        """"""
        profiles = [ProfileFactory() for i in range(3)]
        infrastructure = InfrastructureFactory(editable_by=profiles[:2],
                                               accessible_by=profiles[1:])
        self.assertQuerysetEqual(infrastructure.editable_by.all(),
                                 profiles[:2], ordered=False)
        self.assertQuerysetEqual(infrastructure.accessible_by.all(),
                                 profiles[1:], ordered=False)

    def test_capacity(self):
        """"""
        capacity = CapacityFactory()
        print(capacity)
        print(capacity.place)

    def test_fclass(self):
        """"""
        fclass = FClassFactory()
        print(fclass)

    def test_place_field(self):
        """"""
        place_field = PlaceFieldFactory()
        print(place_field)


class TestInfrastructureAPI(_TestAPI, BasicModelTest, APITestCase):
    """"""
    url_key = "infrastructures"
    factory = InfrastructureFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        infrastructure: Infrastructure = cls.obj
        editable_by = infrastructure.editable_by
        accessible_by = infrastructure.accessible_by
        layer = infrastructure.layer.pk
        symbol = infrastructure.symbol.pk

        data = dict(name=faker.word(), description=faker.word(),
                             editable_by=editable_by,
                             accessible_by=accessible_by, layer=layer,
                             symbol=symbol)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
