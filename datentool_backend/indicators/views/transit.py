from django.http import HttpResponse
from django.db import transaction

from io import StringIO
from distutils.util import strtobool
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse


from datentool_backend.population.serializers import MessageSerializer
from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from datentool_backend.indicators.models import (Stop,
                                                 MatrixStopStop,
                                                 Router,
                                                 ModeVariant,
                                                 MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 )
from datentool_backend.indicators.serializers import (StopSerializer,
                                                      UploadStopTemplateSerializer,
                                                      MatrixStopStopSerializer,
                                                      UploadMatrixStopStopTemplateSerializer,
                                                      RouterSerializer,
                                                      MatrixCellPlaceSerializer,
                                                      MatrixCellStopSerializer,
                                                      MatrixPlaceStopSerializer,
                          )
from datentool_backend.population.serializers import drop_constraints



class ExcelTemplateMixin:
    """Mixin to download and upload excel-templates"""

    def get_serializer_class(self):
        """get the serializer_class"""
        return self.serializer_action_classes.get(self.action, self.serializer_class)

    @extend_schema(description='Create Excel-Template to download',
                   request=None,
                   #responses={
                       #(200, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'): bytes
                   #},
                   )

    @action(methods=['POST'], detail=False)
    def create_template(self, request):
        """Download the Stops-Template"""
        serializer = self.get_serializer()
        content = serializer.create_template()
        response = HttpResponse(
            content_type=(
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = \
            'attachment; filename=template.xlsx'
        response.write(content)
        return response

    @extend_schema(description='Upload Excel-File with Stops',
                   request=inline_serializer(
                       name='FileDropConstraintSerializer',
                       fields={'drop_constraints': drop_constraints,
                               'excel_file': serializers.FileField(),
                               }
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Upload successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Upload failed')})
    @action(methods=['POST'], detail=False)
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        qs = self.get_queryset()
        model = qs.model
        manager = model.copymanager
        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        with transaction.atomic():
            if drop_constraints:
                manager.drop_constraints()
                manager.drop_indexes()

            qs.delete()

            try:
                serializer = self.get_serializer()
                df = serializer.read_excel_file(request)

                with StringIO() as file:
                    df.to_csv(file, index=False)
                    file.seek(0)
                    model.copymanager.from_csv(
                        file,
                        drop_constraints=False, drop_indexes=False,
                    )

            except Exception as e:
                msg = str(e)
                return Response({'message': msg,}, status=status.HTTP_406_NOT_ACCEPTABLE)

            finally:
                # recreate indices
                if drop_constraints:
                    manager.restore_constraints()
                    manager.restore_indexes()

        msg = f'Upload successful of {len(df)} rows'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)


class StopViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    serializer_action_classes = {'upload_template': UploadStopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class MatrixStopStopViewSet(ExcelTemplateMixin, ProtectCascadeMixin, viewsets.ModelViewSet):
    serializer_class = MatrixStopStopSerializer
    serializer_action_classes = {'upload_template': UploadMatrixStopStopTemplateSerializer,
                                 }
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixStopStop.objects.filter(variant=variant)


    @extend_schema(description='Upload Excel-File or PTV-Visum-Matrix with Traveltimes from Stop to Stop',
                   request=inline_serializer(
                       name='FileDropConstraintModeVariantSerializer',
                       fields={'drop_constraints': drop_constraints,
                               'variant': serializers.PrimaryKeyRelatedField(
                           queryset=ModeVariant.objects.all(),
                           help_text='mode_variant_id',),
                               'excel_or_visum_file': serializers.FileField(help_text='Excel- or PTV-Visum-Matrix'),
                               },
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Upload successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Upload failed')})
    @action(methods=['POST'], detail=False)
    def upload_template(self, request):
        """Upload the filled out Stops-Template"""
        return super().upload_template(request)


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class AirDistanceRouterMixin:

    @extend_schema(description='Create Traveltime Matrix on AirDistance',
                   request=inline_serializer(
                       name='AirDistanceSerializer',
                       fields={'drop_constraints': drop_constraints,
                               'variant': serializers.PrimaryKeyRelatedField(
                           queryset=ModeVariant.objects.all(),
                           help_text='mode_variant_id',),
                               'speed': serializers.FloatField(),
                               'max_distance': serializers.FloatField(),
                               }
                   ),
                   responses={202: OpenApiResponse(MessageSerializer,
                                                   'Calculation successful'),
                              406: OpenApiResponse(MessageSerializer,
                                                   'Calculation failed')})
    @action(methods=['POST'], detail=False)
    def precalculate_traveltime(self, request):
        """Calculate traveltime with a air distance router"""
        qs = self.get_queryset()
        model = qs.model
        manager = model.copymanager
        drop_constraints = bool(strtobool(
            request.data.get('drop_constraints', 'False')))

        with transaction.atomic():
            if drop_constraints:
                manager.drop_constraints()
                manager.drop_indexes()

            qs.delete()

            try:
                serializer = self.get_serializer()
                df = serializer.calculate_traveltimes(request)

                with StringIO() as file:
                    df.to_csv(file, index=False)
                    file.seek(0)
                    model.copymanager.from_csv(
                        file,
                        drop_constraints=False, drop_indexes=False,
                    )

            except Exception as e:
                msg = str(e)
                return Response({'message': msg,}, status=status.HTTP_406_NOT_ACCEPTABLE)

            finally:
                # recreate indices
                if drop_constraints:
                    manager.restore_constraints()
                    manager.restore_indexes()

        msg = f'Traveltime Calculation successful, added {len(df)} rows'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)


class MatrixCellPlaceViewSet(AirDistanceRouterMixin, ProtectCascadeMixin, viewsets.GenericViewSet):
    serializer_class = MatrixCellPlaceSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixCellPlace.objects.filter(variant=variant)


class MatrixCellStopViewSet(AirDistanceRouterMixin, ProtectCascadeMixin, viewsets.GenericViewSet):
    serializer_class = MatrixCellStopSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixCellStop.objects.filter(variant=variant)


class MatrixPlaceStopViewSet(AirDistanceRouterMixin, ProtectCascadeMixin, viewsets.GenericViewSet):
    serializer_class = MatrixPlaceStopSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    def get_queryset(self):
        variant = self.request.data.get('variant')
        return MatrixPlaceStop.objects.filter(variant=variant)
