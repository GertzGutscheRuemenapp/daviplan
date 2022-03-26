from io import StringIO
import os
from collections import OrderedDict
from typing import Tuple, List
import pandas as pd


from django.conf import settings
from django.db.models.fields import FloatField
from rest_framework import serializers

from openpyxl.utils import get_column_letter, quote_sheetname
from openpyxl import styles
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.dimensions import ColumnDimension, RowDimension
from openpyxl.worksheet.datavalidation import DataValidation

from datentool_backend.area.models import AreaLevel, Area
from datentool_backend.population.models import Population, Prognosis, PopulationEntry



area_level_id_serializer = serializers.PrimaryKeyRelatedField(
    queryset=AreaLevel.objects.all(),
    help_text='area_level_id',)


prognosis_id_serializer = serializers.PrimaryKeyRelatedField(
    queryset=Prognosis.objects.all(),
    help_text='prognosis_id',)


class PopulationTemplateSerializer(serializers.Serializer):
    """Serializer for uploading Population and Prognosis"""
    excel_file = serializers.FileField()
    drop_constraints = serializers.BooleanField(default=True)

    def create_template(self,
                        area_level_id: int,
                        years: List[int],
                        prognosis_id: int,
                        ) -> bytes:
        """Create a template file for population/prognosis"""

        area_level = AreaLevel.objects.get(pk=area_level_id)

        excel_filename = 'Einwohnerrealdaten.xlsx' if prognosis_id is None else 'Prognosedaten.xlsx'

        dv_pos_float = DataValidation(type="decimal",
                                operator="greaterThanOrEqual",
                                formula1=0,
                                allow_blank=True)
        dv_pos_float.error = 'Nur Zahlen >= 0 erlaubt'
        dv_pos_float.title = 'Ungültige positive Zahlen-Werte'

        validations = {}

        fn = os.path.join(settings.MEDIA_ROOT, excel_filename)
        with pd.ExcelWriter(fn, engine='openpyxl') as writer:
            df_meta = pd.DataFrame({'value': [infrastructure_id]},
                                   index=pd.Index(['infrastructure'], name='key'))
            df_meta.to_excel(writer, sheet_name='meta')

            for year in years:

                df_year.to_excel(writer,
                                 sheet_name=year,
                                 freeze_panes=(9, 3))

                ws: Worksheet = writer.sheets.get(year)

                row12 = ws[1:2]
                for row in row12:
                    for cell in row:
                        cell.alignment = styles.Alignment(horizontal='center', wrap_text=True)


                dv.add('G3:H999999')
                ws.add_data_validation(dv_pos_float)

            ws.row_dimensions[3] = RowDimension(ws, index=3, hidden=True)

            ws.column_dimensions['A'] = ColumnDimension(ws, index='A', hidden=True)
            ws.column_dimensions['B'] = ColumnDimension(ws, index='B', width=30)
            for col_no in range(3, len(df_places.columns) + 2):
                col = get_column_letter(col_no)
                ws.column_dimensions[col] = ColumnDimension(ws, index=col, width=16)

        content = open(fn, 'rb').read()
        return content

    def read_excel_file(self, request) -> pd.DataFrame:
        """read excelfile and return a dataframe"""
        excel_file = request.FILES['excel_file']

        # check if the right Excel-File is uploaded
        df_meta = pd.read_excel(excel_file.file,
                           sheet_name='meta').set_index('key')

        df = pd.DataFrame()
        return df
