import os
import json
from test_plus import APITestCase
from django.urls import reverse
from django.contrib.gis.geos import MultiPolygon

from datentool_backend.api_test import LoginTestCase
from datentool_backend.area.models import Area
from datentool_backend.area.factories import AreaLevelFactory
from datentool_backend.site.factories import ProjectSettingFactory


class UploadTest(LoginTestCase, APITestCase):

    testdata_folder = 'testdata'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.can_edit_basedata = True
        cls.profile.save()
        cls.arealevel = AreaLevelFactory()
        # area near Lüneburg (the shapes are placed there)
        ewkt = ('SRID=4326;MultiPolygon (((10.00766777085825865 53.48274493044656452, '
                '10.02453528324792309 53.01694208830124211, '
                '10.62657572546361173 53.13241967312278291, '
                '10.62527822451055926 53.17848095695609345, '
                '10.65860778024205935 53.18659033791266211, '
                '10.65855709661107653 53.19029024297408625, '
                '10.63562782195637979 53.21856157233393958, '
                '10.58956653812306392 53.37555918765312413, '
                '10.00766777085825865 53.48274493044656452)))')
        geom = MultiPolygon.from_ewkt(ewkt)
        ProjectSettingFactory(project_area=geom)

    def test_upload_shape(self):
        # delete areas
        Area.objects.filter(area_level_id=self.arealevel.pk).delete()

        # upload excel-file
        file_name_areas = 'plaene.zip'
        file_path_areas = os.path.join(os.path.dirname(__file__),
                                       self.testdata_folder,
                                       file_name_areas)
        file_content = open(file_path_areas, 'rb')
        data = {
                'file' : file_content,
                'sync' : True,
            }

        url = reverse('arealevels-upload-shapefile',
                      kwargs={'pk': self.arealevel.pk})
        res = self.client.post(url, data,
                               extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)
        self.assertEqual(json.loads(res.content)['message'],
                         'Hochladen der Gebiete gestartet')

        # test if areas > threashold were put into the database
        self.assertEqual(Area.objects.count(), 3)

        # set key and label field
        self.arealevel.key_field = 'ID_TR_Mast'
        self.arealevel.label_field = 'GEN'

        area_qs = Area.label_annotated_qs(self.arealevel)

        # area 1 should not be uploaded, because its intersection with the project area
        # is smaller than the threashold
        self.assertQuerysetEqual(area_qs.filter(ID_TR_Mast=1), [])
        area2 = area_qs.get(ID_TR_Mast=2)
        self.assertEqual(area2.GEN, 'Teilraum Süd')
        self.assertEqual(area2.label, 'Teilraum Süd')
        self.assertEqual(area2.key, '2')
        self.assertEqual(area2.is_cut, False)

        area3 = area_qs.get(ID_TR_Mast=3)
        self.assertEqual(area3.GEN, 'Teilraum Mitte')
        self.assertEqual(area3.label, 'Teilraum Mitte (Ausschnitt)')
        self.assertEqual(area3.key, '3')
        self.assertEqual(area3.is_cut, True)

        area4 = area_qs.get(ID_TR_Mast=4)
        self.assertEqual(area4.label, 'Teilraum West')
        self.assertEqual(area4.is_cut, False)

    def test_upload_geopackage(self):
        Area.objects.filter(area_level_id=self.arealevel.pk).delete()

        # upload excel-file
        file_name_areas = 'Masterplaene.gpkg'
        file_path_areas = os.path.join(os.path.dirname(__file__),
                                            self.testdata_folder,
                                            file_name_areas)
        file_content = open(file_path_areas, 'rb')
        data = {
                'file' : file_content,
                'sync': True,
            }

        url = reverse('arealevels-upload-shapefile',
                      kwargs={'pk': self.arealevel.pk})
        res = self.client.post(url, data,
                               extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)
        self.assertEqual(json.loads(res.content)['message'],
                         'Hochladen der Gebiete gestartet')

        # test if areas > threashold were put into the database
        self.assertEqual(Area.objects.count(), 3)

        # set key and label field
        self.arealevel.key_field = 'ID_TR_Masterplan'
        self.arealevel.label_field = 'GEN'

        area_qs = Area.label_annotated_qs(self.arealevel)
        # area 1 should not be uploaded, because its intersection with the project area
        # is smaller than the threashold
        self.assertQuerysetEqual(area_qs.filter(ID_TR_Masterplan=1), [])
        area3 = area_qs.get(ID_TR_Masterplan=3)
        self.assertEqual(area3.GEN, 'Teilraum Mitte')
        self.assertEqual(area3.label, 'Teilraum Mitte (Ausschnitt)')
        self.assertEqual(area3.key, '3')
        self.assertEqual(area3.is_cut, True)

    def test_upload_broken_data(self):
        Area.objects.filter(area_level_id=self.arealevel.pk).delete()

        # upload excel-file
        file_name_areas = 'Reisezeimatrix_HL_klein.mtx'
        file_path_areas = os.path.join(os.path.dirname(__file__),
                                       self.testdata_folder,
                                       file_name_areas)
        file_content = open(file_path_areas, 'rb')
        data = {
                'file' : file_content,
                'sync': True,
            }

        url = reverse('arealevels-upload-shapefile',
                      kwargs={'pk': self.arealevel.pk})
        res = self.client.post(url, data,
                               extra=dict(format='multipart/form-data'))
        self.assert_http_406_not_acceptable(res, msg=res.content)
