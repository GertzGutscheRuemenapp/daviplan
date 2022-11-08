from typing import Dict, List
import os
from rest_framework import serializers
from .models import SiteSetting, ProjectSetting
from django.db.models import Max, Min, Count, F
from django.conf import settings
import logging

from datentool_backend.utils.geometry_fields import MultiPolygonGeometrySRIDField
from datentool_backend.modes.models import Mode
from datentool_backend.models import (DemandRateSet, Prognosis, ModeVariant,
                                      Year, AreaLevel, Area)
from datentool_backend.utils.processes import (ProtectedProcessManager,
                                               ProcessScope)

from datentool_backend.indicators.models import (MatrixCellPlace,
                                                 MatrixCellStop,
                                                 MatrixPlaceStop,
                                                 MatrixStopStop,
                                                 Stop,
                                                 )

logger = logging.getLogger('areas')



class YearSerializer(serializers.ModelSerializer):
    has_real_data = serializers.BooleanField(source='has_real',
                                             read_only=True)
    has_prognosis_data = serializers.BooleanField(source='has_prognosis',
                                                  read_only=True)
    has_statistics_data = serializers.BooleanField(source='has_statistics',
                                                   read_only=True)
    class Meta:
        model = Year
        fields = ('id', 'year', 'is_prognosis', 'is_real',
                  'has_real_data', 'has_prognosis_data', 'has_statistics_data')


class ProjectSettingSerializer(serializers.ModelSerializer):
    project_area = MultiPolygonGeometrySRIDField(srid=3857)
    start_year = serializers.SerializerMethodField(read_only=True)
    end_year = serializers.SerializerMethodField(read_only=True)
    min_year = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProjectSetting
        fields = ('project_area', 'start_year', 'end_year', 'min_year')

    def get_start_year(self, obj):
        agg = Year.objects.all().aggregate(Min('year'))
        return agg['year__min']

    def get_end_year(self, obj):
        agg = Year.objects.all().aggregate(Max('year'))
        return agg['year__max']

    def get_min_year(self, obj):
        return Year.MIN_YEAR


class BaseDataSettingSerializer(serializers.Serializer):
    pop_area_level = serializers.SerializerMethodField(read_only=True)
    pop_statistics_area_level = serializers.SerializerMethodField(read_only=True)
    default_demand_rate_sets = serializers.SerializerMethodField(read_only=True)
    default_mode_variants = serializers.SerializerMethodField(read_only=True)
    default_prognosis = serializers.SerializerMethodField(read_only=True)
    routing = serializers.SerializerMethodField(read_only=True)
    processes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = ('default_pop_area_level', 'pop_statistics_area_level',
                  'default_demand_rate_sets', 'default_mode_variants',
                  'default_prognosis')

    # ToDo: what in case get returns multiple objects?
    # (is the case for all default functions here, but should already be
    # prevented in model)
    def get_pop_statistics_area_level(self, obj) -> int:
        try:
            level = AreaLevel.objects.get(is_statistic_level=True)
            return level.id
        except AreaLevel.DoesNotExist:
            return

    def get_pop_area_level(self, obj) -> int:
        try:
            level = AreaLevel.objects.get(is_pop_level=True)
            return level.id
        except AreaLevel.DoesNotExist:
            return

    def get_default_demand_rate_sets(self, obj) -> Dict[int, int]:
        sets = DemandRateSet.objects.filter(
            is_default=True).order_by('service_id')
        ret = [{'service': s.service.id, 'demandrateset': s.id} for s in sets]
        return ret

    def get_default_mode_variants(self, obj) -> Dict[int, int]:
        sets = ModeVariant.objects.filter(network__is_default=True).order_by('mode')
        ret = [{'mode': s.mode, 'variant': s.id} for s in sets]
        return ret

    def get_default_prognosis(self, obj) -> int:
        try:
            prog = Prognosis.objects.get(is_default=True)
            return prog.id
        except Prognosis.DoesNotExist:
            return

    def get_routing(self, obj):
        base_net_existing = os.path.exists(
            os.path.join(settings.MEDIA_ROOT, settings.BASE_PBF))
        project_area_net_existing = os.path.exists(
            os.path.join(settings.MEDIA_ROOT, 'projectarea.pbf'))
        #running = {}
        #for mode in [Mode.WALK, Mode.BIKE, Mode.CAR]:
            #running[mode.name] = OSRMRouter(mode).is_running
        return {
            'base_net': base_net_existing,
            'project_area_net': project_area_net_existing,
            #'running': running,
        }

    def get_processes(self, obj):
        return { ProcessScope(scope).name.lower():
                 ProtectedProcessManager.is_running(ProcessScope(scope))
                 for scope in ProcessScope }


class SiteSettingSerializer(serializers.ModelSerializer):
    #''''''
    #url = serializers.HyperlinkedIdentityField(
        #view_name='settings-detail', read_only=True)

    class Meta:
        model = SiteSetting
        fields = ('name', 'title', 'contact_mail', 'logo',
                  'primary_color', 'secondary_color', 'welcome_text',
                  'bkg_user', 'bkg_password', 'regionalstatistik_user',
                  'regionalstatistik_password')
        extra_kwargs = {
            'bkg_password': {'write_only': True},
            'regionalstatistik_password': {'write_only': True}
        }


class MatrixStatisticsSerializer(serializers.Serializer):
    n_places = serializers.SerializerMethodField(read_only=True)
    n_cells = serializers.SerializerMethodField(read_only=True)
    n_rels_place_cell_modevariant = serializers.SerializerMethodField(read_only=True)
    n_stops = serializers.SerializerMethodField(read_only=True)
    n_rels_place_stop_modevariant = serializers.SerializerMethodField(read_only=True)
    n_rels_stop_cell_modevariant = serializers.SerializerMethodField(read_only=True)
    n_rels_stop_stop_modevariant = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = ('n_places',
                  'n_cells',
                  'n_rels_place_cell_walk',
                  'n_rels_place_cell_bike',
                  'n_rels_place_cell_car',
                  'n_rels_place_cell_transit',
                  'n_stops',
                  'n_rels_place_stop_transit',
                  'n_rels_stop_cell_transit',
                  'n_rels_stop_stop_transit',
                  )

    def get_n_places(self, obj) -> int:
            return MatrixCellPlace.objects.distinct('place_id').count()

    def get_n_cells(self, obj) -> int:
            return MatrixCellPlace.objects.distinct('cell_id').count()

    def get_n_rels_place_cell_modevariant(self, obj) -> Dict[int, int]:
            qs = MatrixCellPlace.objects\
                .values('variant')\
                .annotate(n_relations=Count('variant'))
            return {var['variant']: var['n_relations']
                    for var in qs}

    def get_n_stops(self, obj) -> int:
            return Stop.objects.count()

    def get_n_rels_place_stop_modevariant(self, obj) -> Dict[int, int]:
        qs = MatrixPlaceStop.objects\
            .values('variant')\
            .annotate(n_relations=Count('variant'))
        return {var['variant']: var['n_relations']
                for var in qs}

    def get_n_rels_stop_cell_modevariant(self, obj) -> Dict[int, int]:
        qs = MatrixCellStop.objects\
            .values('variant')\
            .annotate(n_relations=Count('variant'))
        return {var['variant']: var['n_relations']
                for var in qs}

    def get_n_rels_stop_stop_modevariant(self, obj) -> Dict[int, int]:
        qs = MatrixStopStop.objects\
            .values('variant')\
            .annotate(n_relations=Count('variant'))
        return {var['variant']: var['n_relations']
                for var in qs}

