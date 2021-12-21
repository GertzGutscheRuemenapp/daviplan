from collections import OrderedDict
import json
from unittest import skip
from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelTest
from datentool_backend.area.tests import _TestAPI, _TestPermissions
from datentool_backend.user.factories import ProfileFactory

from datentool_backend.infrastructure.factories import (InfrastructureFactory, ServiceFactory, CapacityFactory,
                        FClassFactory, PlaceFieldFactory, PlaceFactory,
                        FieldTypeFactory)
from datentool_backend.infrastructure.models import (Infrastructure, Place, Capacity, FieldTypes, FClass,
                     Service, PlaceField)


from faker import Faker

faker = Faker('de-DE')


class TestInfrastructure(TestCase):

    def test_service(self):
        service = ServiceFactory()
        print(service.quota_type)

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


class TestInfrastructureAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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

    @skip('not fixed yet')
    def test_can_edit_basedata(self):
        pass


    #def test_admin_access(self):
        #"""write permission if user has admin_access"""
        #super().admin_access()

    #def test_can_patch_symbol(self):
        #"""user, who can_edit_basedata have the permission to patch the symbol"""
        #profile = self.profile
        #original_permission = profile.can_edit_basedata

        ## Testprofile, with permission to edit basedata
        #profile.can_edit_basedata = True
        #profile.save()

        ##patch_data3 = self.patch_data.copy()
        ##patch_data3['symbol'] = 1
        ##self.patch_data = patch_data3
        #self.test_put_patch()

        ## Testprofile, without permission to edit basedata
        #profile.can_edit_basedata = False
        #profile.save()
        #self.test_put_patch()



class TestServiceAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "services"
    factory = ServiceFactory


    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service: Service = cls.obj
        infrastructure = service.infrastructure.pk
        editable_by = list(service.editable_by.all().values_list(flat=True))
        #quota_id = service.pk

        data = dict(name=faker.word(),
                    description=faker.word(),
                    infrastructure=infrastructure,
                    editable_by=editable_by,
                    capacity_singular_unit=faker.word(),
                    capacity_plural_unit=faker.word(),
                    has_capacity=True,
                    demand_singular_unit=faker.word(),
                    demand_plural_unit=faker.word(),
                    #quota_id=quota_id,
                    quota_type=faker.word())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPlaceAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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


class TestCapacityAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
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


class TestFieldTypeNUMSTRAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "fieldtypes"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.obj = FieldTypeFactory(field_type=FieldTypes.NUMBER)
        data = dict(field_type=FieldTypes.NUMBER,
                    name=faker.word(),
                    )
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestFieldTypeCLAAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "fieldtypes"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.obj = FieldTypeFactory(field_type=FieldTypes.CLASSIFICATION)
        #fclasses = [FClassFactory(classification=cls.obj),
                    #FClassFactory(classification=cls.obj)]

        fclass_set = [{'order': 1, 'value': faker.word(), },
                      {'order': 2, 'value': faker.word(), },
                      ]

        data = dict(field_type=FieldTypes.CLASSIFICATION,
                    name=faker.word(),
                    classification=fclass_set,
                    )

        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data

    def test_patch_fclass_with_deletion(self):
        """test also, if deletion works"""

        field_typ = FieldTypeFactory(field_type=FieldTypes.CLASSIFICATION)
        fclass1 = FClassFactory(classification=field_typ, order=7, value='7')
        fclass2 = FClassFactory(classification=field_typ, order=42, value='42')

        self.assertEqual(field_typ.fclass_set.count(), 2)

        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': field_typ.pk, }
        formatjson = dict(format='json')

        # patch the fclass-set with new data

        fclass_set = [{'order': 42, 'value': '422', },
                      {'order': 2, 'value': '2', },
                      {'order': 3, 'value': '3', },
                      ]

        patch_data = dict(classification=fclass_set)
        # check status code for patch
        response = self.patch(url, **kwargs,
                              data=patch_data, extra=formatjson)
        self.response_200(msg=response.content)

        # test if fclasses are correctly updated, added and deleted
        new_fclass_set = field_typ.fclass_set.all()
        self.assertEqual(len(new_fclass_set), 3)
        # check if the 7 is deleted
        self.assertQuerysetEqual(new_fclass_set.filter(order=7), [])
        self.assertEqual(new_fclass_set.get(order=42).value, '422')
        self.assertEqual(new_fclass_set.get(order=2).value, '2')
        self.assertEqual(new_fclass_set.get(order=3).value, '3')


class TestFClassAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "fclasses"
    factory = FClassFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        fclass: FClass = cls.obj
        classification = fclass.classification.pk
        data = dict(classification_id=classification,
                    order=faker.unique.pyint(max_value=100),
                    value=faker.unique.word())
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data


class TestPlaceFieldAPI(_TestPermissions, _TestAPI, BasicModelTest, APITestCase):
    """Test to post, put and patch data"""
    url_key = "placefields"
    factory = PlaceFieldFactory

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        placefield: PlaceField = cls.obj
        infrastructure = placefield.infrastructure.pk
        field_type = placefield.field_type.pk
        data = dict(attribute=faker.unique.word(), unit=faker.word(),
                    infrastructure=infrastructure,
                    field_type=field_type)
        cls.post_data = data
        cls.put_data = data
        cls.patch_data = data
