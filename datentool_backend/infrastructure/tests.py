from collections import OrderedDict
from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI
from ..user.factories import ProfileFactory

from .factories import (InfrastructureFactory, ServiceFactory, CapacityFactory,
                        FClassFactory, PlaceFieldFactory, PlaceFactory,
                        FieldTypeFactory)
from .models import Infrastructure, Place, Capacity, FieldTypes, FClass


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
    """Test to post, put and patch data"""
    url_key = "infrastructures"
    factory = InfrastructureFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        infrastructure: Infrastructure = cls.obj
        editable_by = list(infrastructure.editable_by.all().values_list(flat=True))
        accessible_by = list(infrastructure.accessible_by.all().values_list(flat=True))
        layer = infrastructure.layer.pk
        symbol = infrastructure.symbol.pk

        data = dict(name=faker.word(), description=faker.word(),
                             editable_by=editable_by,
                             accessible_by=accessible_by, layer=layer,
                             symbol=symbol)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_patch_empty_editable_by(self):
        """Test the patch with an empty list"""
        patch_data2 = self.patch_data.copy()
        patch_data2['editable_by'] = []
        patch_data2['accessible_by'] = []
        self.patch_data = patch_data2
        super().test_put_patch()


class TestPlaceAPI(_TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "places"
    factory = PlaceFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        place: Place = cls.obj
        infrastructure = place.infrastructure.pk
        geom = place.geom.ewkt

        properties = OrderedDict(
            name=faker.word(),
            infrastructure=infrastructure,
            attributes=faker.json(),
        )
        geojson = {
            'type': 'Feature',
            'geometry': geom,
            'properties': properties,
        }

        cls.post_data = geojson
        geojson_putpatch = geojson.copy()
        geojson_putpatch['id'] = place.id

        cls.put_data = geojson_putpatch
        cls.patch_data = geojson_putpatch


class TestCapacityAPI(_TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "capacities"
    factory = CapacityFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        capacity: Capacity = cls.obj
        place = capacity.place.pk
        service = capacity.service.pk

        data = dict(place=place, service=service,
                    capacity=faker.pyfloat(positive=True), from_year=faker.year())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestFieldTypeAPI(_TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "fieldtypes"
    factory = FieldTypeFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        data = dict(field_type=faker.random_element(FieldTypes),
                    name=faker.word())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestFClassAPI(_TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "fclasses"
    factory = FClassFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        fclass: FClass = cls.obj
        classification = fclass.classification.pk
        data = dict(classification=classification,
                    order=faker.unique.pyint(max_value=100),
                    value=faker.unique.word())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
