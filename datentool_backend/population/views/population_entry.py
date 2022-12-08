import pandas as pd
import math
from io import StringIO
from django.http.request import QueryDict
from django_filters import rest_framework as filters
from django.db.models import Max, Min

from openpyxl.reader.excel import load_workbook

from drf_spectacular.utils import (extend_schema,
                                   OpenApiResponse,
                                   inline_serializer)
from djangorestframework_camel_case.parser import CamelCaseMultiPartParser
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.core.exceptions import PermissionDenied, BadRequest
from rest_framework.response import Response

from datentool_backend.utils.crypto import decrypt
from datentool_backend.utils.excel_template import (ColumnError,
                                                    write_template_df,
                                                    ExcelTemplateMixin)

from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, HasAdminAccess, CanEditBasedata)
from datentool_backend.utils.pop_aggregation import (
    intersect_areas_with_raster, aggregate_population, aggregate_many,
    disaggregate_population)
from datentool_backend.utils.regionalstatistik import Regionalstatistik
from datentool_backend.population.models import (
    PopulationRaster,
    Prognosis,
    Population,
    PopulationEntry,
    RasterCellPopulationAgeGender,
    AreaCell,
    Year
)

from datentool_backend.demand.constants import RegStatAgeGroups, regstatgenders
from datentool_backend.demand.models import AgeGroup
from datentool_backend.utils.serializers import (MessageSerializer,
                                                 use_intersected_data,
                                                 drop_constraints,
                                                 area_level)
from datentool_backend.population.serializers import (
    PrognosisSerializer,
    PopulationSerializer,
    PopulationDetailSerializer,
    PopulationEntrySerializer,
    PopulationTemplateSerializer,
    prognosis_id_serializer,
    area_level_id_serializer,
    years_serializer,
    get_area_level_key,
)
from datentool_backend.site.models import SiteSetting
from datentool_backend.area.models import Area, AreaLevel
from datentool_backend.utils.processes import (ProcessScope,
                                               ProtectedProcessManager)

import logging

logger = logging.getLogger('population')


class PopulationEntryViewSet(ExcelTemplateMixin, viewsets.ModelViewSet):
    queryset = PopulationEntry.objects.all()
    serializer_class = PopulationEntrySerializer
    serializer_action_classes = {'create_template': PopulationTemplateSerializer,
                                 'upload_template': PopulationTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
    filterset_fields = ['population']

    @extend_schema(description='Upload Population Template',
                   request=inline_serializer(
                       name='PopulationUploadTemplateSerializer',
                       fields={
                           'area_level': area_level_id_serializer,
                           'years': years_serializer,
                           'prognosis': prognosis_id_serializer,
                           'drop_constraints': drop_constraints
                       }
                       ),
                   )
    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccess | CanEditBasedata])
    def create_template(self, request, **kwargs):
        area_level_id = request.data.get('area_level')
        prognosis_id = request.data.get('prognosis')
        years = request.data.get('years')
        if not years:
            msg = f'Kein Jahr ausgewählt, daher kann kein Template erzeugt werden.'
            logger.error(msg)
            raise BadRequest(msg)
        return super().create_template(request,
                                       area_level_id=area_level_id,
                                       years=years,
                                       prognosis_id=prognosis_id,
                                       )

    @action(methods=['POST'], detail=False,
            permission_classes=[HasAdminAccess | CanEditBasedata],
            parser_classes=[CamelCaseMultiPartParser])
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        return super().upload_template(request)

    def get_read_excel_params(self, request) -> Dict:
        params = dict()
        params['excel_file'] = request.FILES['excel_file']
        params['prognosis_id'] = request.data.get('prognosis')
        return params

    @staticmethod
    def process_excelfile(df: pd.DataFrame,
                          queryset,
                          logger,
                          excel_file,
                          prognosis_id,
                          drop_constraints=False,
                   ):
        # read excelfile
        try:
            logger.info('Lese Excel-Datei')
            df = read_excel_file(excel_file, prognosis_id)
        except (ColumnError, AssertionError, ValueError, ConnectionError) as e:
            msg = str(e)# f'{e} Bitte überprüfen Sie das Template.'
            logger.error(msg)
            return Response({'Fehler': msg},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # write_df
        write_template_df(df, queryset, logger, drop_constraints=drop_constraints)
        # postprocess (optional)
        post_processing(dataframe=df, drop_constraints=drop_constraints, logger=logger)


def read_excel_file(excel_file, prognosis_id) -> pd.DataFrame:
    """read excelfile and return a dataframe"""

    columns = ['population_id', 'area_id', 'gender_id',
               'age_group_id', 'value']
    df = pd.DataFrame(columns=columns)

    wb = load_workbook(excel_file.file)
    meta = wb['meta']
    area_level = AreaLevel.objects.get(is_default_pop_level=True)

    areas = Area.annotated_qs(area_level)
    key_attr = get_area_level_key(logger, area_level)
    df_areas = pd.DataFrame(areas.values(key_attr, 'id'))\
        .set_index(key_attr)\
        .rename(columns={'id': 'area_id', })

    df_genders = pd.DataFrame(Gender.objects.values('id', 'name'))\
        .set_index('name')\
        .rename(columns={'id': 'gender_id', })
    df_agegroups = pd.DataFrame([[ag.id, ag.name] for
                                 ag in AgeGroup.objects.all()],
                                columns=['age_group_id', 'Altersgruppe'])\
        .set_index('Altersgruppe')

    n_years = meta['B2'].value
    years = [meta.cell(3, n).value for n in range(2, n_years + 2)]
    populations = []
    for y in years:
        if not str(y) in wb.sheetnames:
            logger.info(f'Excel-Blatt für Jahr {y} nicht vorhanden')
            continue
        year, created = Year.objects.get_or_create(year=y)
        population, created = Population.objects.get_or_create(
            prognosis_id=prognosis_id,
            year=year,
        )
        try:
            # get the values and unpivot the data
            df_pop = pd.read_excel(excel_file.file,
                                   sheet_name=str(y),
                                   header=[1, 2, 3, 4],
                                   dtype={key_attr: object,},
                                   index_col=[0, 1])\
                .stack(level=[0, 1, 2, 3])\
                .reset_index()
            df_pop = df_pop.drop(['gender_id', 'age_group_id'], axis=1)
            df_pop = df_pop\
                .merge(df_areas, left_on=key_attr, right_index=True)\
                .merge(df_genders, left_on='Geschlecht', right_index=True)\
                .merge(df_agegroups, left_on='Altersgruppe', right_index=True)

            df_pop.rename(columns={0: 'value',}, inplace=True)
            df_pop['population_id'] = population.id
        except KeyError as e:
            raise ColumnError(f'Spalte {e} wurde nicht gefunden.')
        populations.append(population)
        df = pd.concat([df, df_pop[columns]])

    return df


def post_processing(dataframe, drop_constraints=False,
                    logger=logging.getLogger('population')):
    populations = Population.objects.filter(
        id__in=dataframe['population_id'].unique())
    logger.info('Disaggregiere Bevölkerungsdaten')
    for i, population in enumerate(populations):
        disaggregate_population(population, use_intersected_data=True,
                                drop_constraints=drop_constraints)
        logger.info(f'{i + 1}/{len(populations)}')
    logger.info('Aggregiere Bevölkerungsdaten')
    aggregate_many(AreaLevel.objects.all(), populations,
                   drop_constraints=drop_constraints)
