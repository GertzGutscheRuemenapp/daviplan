from rest_framework import viewsets

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from .models import (Stop,
                     Router,
                     Indicator,
                     IndicatorType,
                     )
from .compute import ComputeIndicator
from .serializers import (StopSerializer,
                          RouterSerializer,
                          IndicatorSerializer,
                          AreaIndicatorSerializer,
                          )


class StopViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class IndicatorViewSet(viewsets.ModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class AreaIndicatorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AreaIndicatorSerializer

    def get_queryset(self):
        #  filter the capacity returned for the specific service
        indicator_id = self.request.query_params.get('indicator')

        classname = Indicator.objects.get(pk=indicator_id).indicator_type.classname
        compute_class: ComputeIndicator = IndicatorType._indicator_classes[classname]
        qs = compute_class(self.request.query_params).compute()
        return qs
