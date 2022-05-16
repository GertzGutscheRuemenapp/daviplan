import os
from io import BytesIO

import pandas as pd
from openpyxl.reader.excel import load_workbook

from django.urls import reverse
from test_plus import APITestCase

from datentool_backend.api_test import LoginTestCase
from datentool_backend.infrastructure.factories import (InfrastructureFactory,
                                                        ServiceFactory,
                                                        Place,
                                                        CapacityFactory,
                                                        PlaceFieldFactory,
                                                        FieldTypeFactory,
                                                        PlaceFactory,
                                                        )

from datentool_backend.area.models import FieldTypes
from datentool_backend.area.factories import FClassFactory


class InfrastructureTemplateTest(LoginTestCase, APITestCase):

    testdata_folder = 'testdata'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.can_edit_basedata = True
        cls.profile.save()
        cls.infra = InfrastructureFactory(id=1)
        cls.service1 = ServiceFactory(name='Schulen',
                                      has_capacity=False,
                                      infrastructure=cls.infra)
        cls.service2 = ServiceFactory(name='Schulplätze',
                                      has_capacity=True,
                                      infrastructure=cls.infra)

        #cls.str_field = PlaceFieldFactory(infrastructure=cls.infra,
                                          #field_type__name='PlaceName',
                                          #field_type__ftype=FieldTypes.STRING,
                                          #name='Bezeichnung',
                                          #is_label=True)
        cls.hnr_field = PlaceFieldFactory(infrastructure=cls.infra,
                                          field_type__name='Hnr',
                                          name='Hausnummer',
                                          field_type__ftype=FieldTypes.STRING)
        cls.num_field = PlaceFieldFactory(infrastructure=cls.infra,
                                          field_type__name='FloatType',
                                          name='Gewichtung',
                                          field_type__ftype=FieldTypes.NUMBER)

        cl_ft1 = FieldTypeFactory(ftype=FieldTypes.CLASSIFICATION, name='Ziffern')
        cl_ft2 = FieldTypeFactory(ftype=FieldTypes.CLASSIFICATION, name='Buchstaben')
        cls.cla_field = PlaceFieldFactory(infrastructure=cls.infra,
                                          name='EinsZweiDrei',
                                          field_type=cl_ft1)

        cv11 = FClassFactory(ftype=cls.cla_field.field_type, value='Eins', order=1)
        cv12 = FClassFactory(ftype=cls.cla_field.field_type, value='Zwei', order=2)
        cv13 = FClassFactory(ftype=cls.cla_field.field_type, value='Drei', order=3)

        cls.cla_field2 = PlaceFieldFactory(infrastructure=cls.infra,
                                           name='AABB',
                                           field_type=cl_ft2)

        cv21 = FClassFactory(ftype=cls.cla_field2.field_type, value='AA', order=1)
        cv22 = FClassFactory(ftype=cls.cla_field2.field_type, value='BB', order=2)

        place1 = PlaceFactory(infrastructure=cls.infra,
                              name='Place1',
                              attributes={
            cls.num_field.name: 1234,
            cls.hnr_field.name: '44b',
            cls.cla_field.name: 'Zwei',
            cls.cla_field2.name: 'BB',
        })
        place2 = PlaceFactory(infrastructure=cls.infra,
                              name='Place2',
                              attributes={
            cls.num_field.name: 567,
            cls.hnr_field.name: '33',
            cls.cla_field.name: 'Drei',
        })

        CapacityFactory(service=cls.service1, place=place1, capacity=1)
        CapacityFactory(service=cls.service1, place=place2, capacity=0)
        CapacityFactory(service=cls.service2, place=place1, capacity=55.5)
        CapacityFactory(service=cls.service2, place=place2, capacity=0)

    def test_create_infrastructure_template(self):
        url = reverse('places-create-template')
        res = self.post(url, data={'infrastructure': self.infra.pk,})
        self.assert_http_200_ok(res)
        wb = load_workbook(BytesIO(res.content))
        self.assertSetEqual(set(wb.sheetnames),
                            {'Standorte und Kapazitäten', 'meta', 'Klassifizierungen'})

    def test_upload_place_template(self):
        """
        test bulk upload places and capacities
        """
        # delete places
        Place.objects.first().delete()

        # upload excel-file
        file_name_places = 'Standorte_und_Kapazitäten_mod.xlsx'
        file_path_places = os.path.join(os.path.dirname(__file__),
                                        self.testdata_folder,
                                        file_name_places)
        file_content = open(file_path_places, 'rb')
        data = {
            'excel_file' : file_content,
            #'infrastructure': self.infra.pk,
        }

        url = reverse('places-upload-template')
        res = self.client.post(url, data,
                               extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)

        df = pd.read_excel(file_path_places, sheet_name='Standorte und Kapazitäten',
                           skiprows=[1, 2]).set_index('Unnamed: 0')

        places = Place.objects.filter(infrastructure=self.infra)
        place_names = places.values_list('name', flat=True)
        assert set(df['Name']).issubset(place_names),\
               'place names in excel_file are not uploaded correcty'

        for place_id, place_row in df.iterrows():
            place = Place.objects.get(infrastructure=self.infra, name=place_row['Name'])
            coords = place.geom.transform(4326, clone=True).coords
            for i, c in enumerate(['Lon', 'Lat']):
                self.assertAlmostEqual(coords[i], place_row.loc[c])
            for place_attr in place.placeattribute_set.all():
                value = place_row.get(place_attr.field.name)
                if place_attr.field.field_type.ftype in [FieldTypes.STRING,
                                                         FieldTypes.CLASSIFICATION]:
                    value = str(value)
                self.assertAlmostEqual(place_attr.value, value)
            for capacity in place.capacity_set.all():
                service = capacity.service
                if service.has_capacity:
                    col = f'Kapazität für Leistung {service.name}'
                else:
                    col = f'Bietet Leistung {service.name} an'
                value = place_row.loc[col]
                self.assertAlmostEqual(capacity.capacity, value)
