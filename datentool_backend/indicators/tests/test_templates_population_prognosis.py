import os
from unittest import skip
from io import BytesIO
from openpyxl.reader.excel import load_workbook
import pandas as pd

from django.urls import reverse
from test_plus import APITestCase

from datentool_backend.indicators.tests.setup_testdata import CreateTestdataMixin
from datentool_backend.api_test import LoginTestCase

from datentool_backend.user.factories import YearFactory
from datentool_backend.demand.factories import GenderFactory, AgeGroup
from datentool_backend.area.factories import (AreaLevelFactory,
                                              AreaFactory,
                                              AreaFieldFactory,
                                              FieldTypeFactory,
                                              FieldTypes)


from datentool_backend.population.factories import (PopulationRasterFactory,
                                                    PopulationFactory,
                                                    PrognosisFactory)


class PopulationTemplateTest(LoginTestCase, APITestCase, CreateTestdataMixin):

    testdata_folder = 'testdata'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.can_edit_basedata = True
        cls.profile.save()

        cls.genders = [GenderFactory(name=n) for n in ['männlich', 'weiblich']]
        AgeGroup.objects.create(from_age=0, to_age=17)
        AgeGroup.objects.create(from_age=18, to_age=64)
        AgeGroup.objects.create(from_age=65, to_age=120)

        cls.age_groups = AgeGroup.objects.all()

        cls.popraster = PopulationRasterFactory()

        cls.years = [YearFactory(year=y, is_default=(y==2022))
                     for y in range(2015, 2023)]
        for year in cls.years:
            PopulationFactory(popraster=cls.popraster, year=year, prognosis=None)

        cls.prognosis = PrognosisFactory(name='Trendentwicklung', is_default=True)
        cls.prognosis_years = [YearFactory(year=y) for y in range(2025, 2045, 5)]
        for year in cls.prognosis_years:
            PopulationFactory(popraster=cls.popraster, year=year, prognosis=cls.prognosis)

        cls.area_level = AreaLevelFactory(name='Gemeinden')

        str_field = FieldTypeFactory(ftype=FieldTypes.STRING)

        cls.gen = AreaFieldFactory(field_type=str_field,
                                   area_level=cls.area_level,
                                   name='gen',
                                   is_label=True)
        cls.rs = AreaFieldFactory(field_type=str_field,
                                  area_level=cls.area_level,
                                  name='rs',
                                  is_key=True)

        areas = [['010030000000', 'Lübeck'],
                 ['010530090090', 'Mölln'],
                 ['010530100100', 'Ratzeburg'],
                 ['010535308008', 'Behlendorf'],
                 ['010535308009', 'Berkenthin'],
                 ]

        for rs, gen in areas:
            area = AreaFactory(area_level=cls.area_level)
            area.attributes = {'rs': rs, 'gen': gen,}


    def test_create_population_template(self):
        url = reverse('populationentries-create-template')
        years = [y.year for y in self.years]
        res = self.post(url, data={'area_level_id': self.area_level.pk,
                                   'years': years,
                                   },
                             extra=dict(format='json')
                             )
        self.assert_http_200_ok(res)
        wb = load_workbook(BytesIO(res.content))
        self.assertSetEqual(set(wb.sheetnames),
                            set(['meta']+[f'{y}' for y in years]))

    def test_create_prognosis_template(self):
        url = reverse('populationentries-create-template')
        years = [y.year for y in self.prognosis_years]
        res = self.post(url, data={'area_level_id': self.area_level.pk,
                                   'years': years,
                                   'prognosis_id': self.prognosis.pk,},
                             extra=dict(format='json')
                             )
        self.assert_http_200_ok(res)
        wb = load_workbook(BytesIO(res.content))
        self.assertSetEqual(set(wb.sheetnames),
                            set(['meta']+[f'{y}' for y in years]))

    @skip('not implemented yet')
    def test_upload_prognosis_template(self):
        """
        test bulk upload population_entries
        """
        ## delete places
        #Place.objects.first().delete()

        ## upload excel-file
        #file_name_places = 'Standorte_und_Kapazitäten_mod.xlsx'
        #file_path_places = os.path.join(os.path.dirname(__file__),
                                        #self.testdata_folder,
                                        #file_name_places)
        #file_content = open(file_path_places, 'rb')
        #data = {
            #'excel_file' : file_content,
            #'infrastructure_id': self.infra.pk,
        #}

        #url = reverse('places-upload-template')
        #res = self.client.post(url, data,
                               #extra=dict(format='multipart/form-data'))
        #self.assert_http_202_accepted(res, msg=res.content)

        #df = pd.read_excel(file_path_places, sheet_name='Standorte und Kapazitäten',
                           #skiprows=[1, 2]).set_index('Unnamed: 0')

        #places = Place.objects.filter(infrastructure=self.infra)
        #place_names = places.values_list('name', flat=True)
        #assert set(df['Name']).issubset(place_names),\
               #'place names in excel_file are not uploaded correcty'

        #for place_id, place_row in df.iterrows():
            #place = Place.objects.get(infrastructure=self.infra, name=place_row['Name'])
            #coords = place.geom.transform(4326, clone=True).coords
            #for i, c in enumerate(['Lon', 'Lat']):
                #self.assertAlmostEqual(coords[i], place_row.loc[c])
            #for place_attr in place.placeattribute_set.all():
                #value = place_row.get(place_attr.field.name)
                #if place_attr.field.field_type.ftype in [FieldTypes.STRING,
                                                         #FieldTypes.CLASSIFICATION]:
                    #value = str(value)
                #self.assertAlmostEqual(place_attr.value, value)
            #for capacity in place.capacity_set.all():
                #service = capacity.service
                #if service.has_capacity:
                    #col = f'Kapazität für Leistung {service.name}'
                #else:
                    #col = f'Bietet Leistung {service.name} an'
                #value = place_row.loc[col]
                #self.assertAlmostEqual(capacity.capacity, value)
