import os
from io import BytesIO
from openpyxl.reader.excel import load_workbook
import pandas as pd
from unittest import skip
from rest_framework import status
from django.urls import reverse
from test_plus import APITestCase
from datentool_backend.api_test import LoginTestCase


class StopTemplateTest(LoginTestCase, APITestCase):

    testdata_folder = 'data'
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
        self.assertListEqual(wb.sheetnames, ['Sheet'])

    @skip('not implemented yet')
    def test_upload_template(self):
        """
        test bulk upload stops
        """
        file_path_stops = os.path.join(os.path.dirname(__file__),
                                    self.testdata_folder,
                                    self.filename_stops)
        data = {
            'bulk_upload' : open(file_path_stops, 'rb'),
        }



        res = self.client.post(self.stops_url, data)
        res_json = res.json()
        assert res.status_code == status.HTTP_201_CREATED
        assert res_json['count'] == len(file_codes)
        assert len(res_json['created']) == len(new_codes)


    @skip('not implemented yet')
    def test_upload_broken_file(self):
        """
        test errors in upload files
        """
        file_path = os.path.join(os.path.dirname(__file__),
                                 self.testdata_folder,
                                 self.filename_stops_errors)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }
        res = self.client.post(self.stops_url, data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
