import os
from test_plus import APITestCase
from django.urls import reverse

from datentool_backend.api_test import LoginTestCase
from datentool_backend.area.models import Area
from datentool_backend.area.factories import AreaLevelFactory


class UploadTest(LoginTestCase, APITestCase):

    testdata_folder = 'testdata'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile.can_edit_basedata = True
        cls.profile.save()
        cls.arealevel = AreaLevelFactory()

    def test_upload_shape(self):
        # delete areas
        Area.objects.filter(area_level_id=self.arealevel.pk).delete()

        # upload excel-file
        file_name_areas = 'Testupload_shape.shp.zip'
        file_path_areas = os.path.join(os.path.dirname(__file__),
                                       self.testdata_folder,
                                       file_name_areas)
        file_content = open(file_path_areas, 'rb')
        data = {
                'file' : file_content,
            }

        url = reverse('arealevels-upload-shapefile',
                      kwargs={'pk': self.arealevel.pk})
        res = self.client.post(url, data,
                               extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)
        # ToDo: test if areas were put into the database
        print(res.content)

    def test_upload_geopackage(self):
        Area.objects.filter(area_level_id=self.arealevel.pk).delete()

        # upload excel-file
        file_name_areas = 'Testupload_geopackage.gpkg'
        file_path_areas = os.path.join(os.path.dirname(__file__),
                                            self.testdata_folder,
                                            file_name_areas)
        file_content = open(file_path_areas, 'rb')
        data = {
                'file' : file_content,
            }

        url = reverse('arealevels-upload-shapefile',
                      kwargs={'pk': self.arealevel.pk})
        res = self.client.post(url, data,
                               extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)
        # ToDo: test if areas were put into the database
        print(res.content)

    def test_upload_broken_data(self):
        Area.objects.filter(area_level_id=self.arealevel.pk).delete()

        # upload excel-file
        file_name_areas = 'Reisezeimatrix_HL_klein.mtx'
        file_path_areas = os.path.join(os.path.dirname(__file__),
                                       self.testdata_folder,
                                       file_name_areas)
        file_content = open(file_path_areas, 'rb')
        data = {
                'file' : file_content
            }

        url = reverse('arealevels-upload-shapefile',
                      kwargs={'pk': self.arealevel.pk})
        res = self.client.post(url, data,
                               extra=dict(format='multipart/form-data'))
        self.assert_http_406_not_acceptable(res, msg=res.content)
        print(res.content)
