from django.db.models import OuterRef, Subquery, Count, IntegerField
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from rest_framework import viewsets
from sql_util.utils import SubqueryCount, SubquerySum, Exists

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)

from .models import (Stop,
                     Router,
                     Indicator,
                     )
from .serializers import (StopSerializer,
                          RouterSerializer,
                          IndicatorSerializer,
                          AreaIndicatorSerializer,
                          )

from datentool_backend.area.models import Area
from datentool_backend.infrastructure.models import Place, Capacity


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
        service_id = self.request.query_params.get('service')
        year = self.request.query_params.get('year', 0)
        scenario = self.request.query_params.get('scenario')

        qs = Area.objects.all()

        name_attr = 'name'
        qs = qs.annotate(name=KeyTextTransform(name_attr, 'attributes'))
        capacities = Capacity.objects.all()
        capacities = Capacity.filter_queryset(capacities,
                                              service_id=service_id,
                                              scenario_id=scenario,
                                              year=year,
                                              )\
            .filter(capacity__gt=0)

        places = Place.objects.all()
        places_with_capacity = places.annotate(
            has_capacity=Exists(capacities.filter(place=OuterRef('pk'))))\
            .filter(has_capacity=True)\

        places_in_area = places_with_capacity\
            .filter(geom__intersects=OuterRef('geom'))\
            .annotate(area_id=OuterRef('id'))\
            .values('area_id')\
            .annotate(n_places=Count('*'))\
            .values('n_places')
        qs = qs.annotate(
            value=Subquery(
                places_in_area, output_field=IntegerField()
            )
        )
        return qs
