import os
from io import BytesIO
from openpyxl.reader.excel import load_workbook
import pandas as pd

from django.urls import reverse
from test_plus import APITestCase
from datentool_backend.api_test import LoginTestCase
from datentool_backend.indicators.models import Stop


class StopTemplateTest(LoginTestCase, APITestCase):

    testdata_folder = 'testdata'
    filename_stops = 'Haltestellen.xlsx'
    filename_stops_errors = 'Haltestellen_errors.xlsx'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.stops_url = reverse('stops-list')

    def test_request_templates(self):
        url = reverse('stops-download-template')
        res = self.get_check_200(url)
        wb = load_workbook(BytesIO(res.content))
        self.assertListEqual(wb.sheetnames, ['Haltestellen'])

    def test_upload_template(self):
        """
        test bulk upload stops
        """
        file_path_stops = os.path.join(os.path.dirname(__file__),
                                    self.testdata_folder,
                                    self.filename_stops)
        file_content = open(file_path_stops, 'rb')
        data = {
            'excel_file' : file_content,
        }

        url = reverse('stops-upload-template')
        res = self.client.post(url, data, extra=dict(format='multipart/form-data'))
        self.assert_http_403_forbidden(res)
        file_content.seek(0)
        self.profile.can_edit_basedata = True
        self.profile.save()
        res = self.client.post(url, data, extra=dict(format='multipart/form-data'))
        self.assert_http_202_accepted(res, msg=res.content)
        # 4 stops should have been uploaded with the correct hst-nr and names
        df = pd.read_excel(file_path_stops, skiprows=[1])

        actual = pd.DataFrame(Stop.objects.values('id', 'name')).set_index('id')
        expected = df[['Nr', 'Name']].rename(columns={'Nr': 'id','Name': 'name',}).set_index('id')
        pd.testing.assert_frame_equal(actual, expected)

    def test_upload_broken_file(self):
        """
        test errors in upload files
        """
        file_path = os.path.join(os.path.dirname(__file__),
                                 self.testdata_folder,
                                 self.filename_stops_errors)
        url = reverse('stops-upload-template')
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }
        self.profile.can_edit_basedata = True
        self.profile.save()
        res = self.client.post(url, data, extra=dict(format='multipart/form-data'))
        self.assert_http_406_not_acceptable(res)
        print(res.content)
