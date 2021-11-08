from django.test import TestCase
from ..user.factories import ProfileFactory
from .factories import (InfrastructureFactory, ServiceFactory, CapacityFactory,
                        FClassFactory, PlaceFieldFactory)


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
