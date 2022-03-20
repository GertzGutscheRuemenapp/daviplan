from django.http import HttpResponse
from io import StringIO
import pandas as pd
from django.contrib.gis.geos import Point
from distutils.util import strtobool
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse


from datentool_backend.population.serializers import MessageSerializer
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from datentool_backend.indicators.models import (Stop,
                                                 Router,
                                                 )
from datentool_backend.indicators.serializers import (StopSerializer,
                                                      RouterSerializer,
                                                      UploadStopTemplateSerializer,
                          )


class StopViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_action_classes = {'upload_template': UploadStopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_serializer_class(self):
        """get the serializer_class"""
        return self.serializer_action_classes.get(self.action, StopSerializer)


    @action(methods=['GET'], detail=False)
    def download_template(self, request):
        """Download the Stops-Template"""
        serializer = self.get_serializer()
        content = serializer.create_template()
        response = HttpResponse(
            content_type=(
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = \
            'attachment; filename=template.xlsx'
        response.write(content)
        return response


    @extend_schema(description='Upload Excel-File with Stops',
                   parameters=[
                       OpenApiParameter(name='drop_constraints',
                                        required=False,
                                        type=bool,
                                        default=True,
                                        description='set to false for tests'),
                   ],
                   #request=None,
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Upload successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Upload failed')})
    @action(methods=['POST'], detail=False)
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        Stop.objects.all().delete()
        try:
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file.file,
                               sheet_name='Haltestellen',
                               skiprows=[1])
            df.rename(columns={'Nr': 'id', 'Name': 'name',}, inplace=True)

            # assert the stopnumers are unique
            assert df['id'].is_unique, 'Haltestellennummer ist nicht eindeutig'

            # create points out of Lat/Lon and transform them to WebMercator
            points = [Point(stop['Lon'], stop['Lat'], srid=4326).transform(3857, clone=True)
                      for i, stop in df.iterrows()]
            df['geom'] = points

            # remove Lat and Lon
            del df['Lat']
            del df['Lon']

            drop_constraints = bool(strtobool(
                request.data.get('drop_constraints', 'False')))

            with StringIO() as file:
                df.to_csv(file, index=False)
                file.seek(0)
                Stop.copymanager.from_csv(
                    file,
                    drop_constraints=drop_constraints, drop_indexes=drop_constraints,
                )

        except Exception as e:
            msg = str(e)
            return Response({'message': msg,}, status=status.HTTP_406_NOT_ACCEPTABLE)

        msg = 'Upload successful'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]
