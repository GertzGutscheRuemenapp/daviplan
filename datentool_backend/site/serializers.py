from typing import Dict
from rest_framework import serializers
from .models import SiteSetting, ProjectSetting
from django.db.models import Max, Min

from datentool_backend.utils.geometry_fields import MultiPolygonGeometrySRIDField
from datentool_backend.utils.pop_aggregation import intersect_areas_with_raster
from datentool_backend.area.views import AreaLevelViewSet
from datentool_backend.population.views.raster import PopulationRasterViewSet
from datentool_backend.models import (DemandRateSet, Prognosis, ModeVariant,
                                      Year, AreaLevel, PopulationRaster)


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

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # trigger various calculations on project area change
        if (validated_data.get('project_area')):
            for popraster in PopulationRaster.objects.all():
                PopulationRasterViewSet._intersect_census(
                    popraster, drop_constraints=True)
            for area_level in AreaLevel.objects.filter(is_preset=True):
                try:
                    areas = AreaLevelViewSet._pull_areas(
                        area_level, instance.project_area, truncate=True)
                    intersect_areas_with_raster(areas, drop_constraints=True)
                except:
                    pass
        return instance


class BaseDataSettingSerializer(serializers.Serializer):
    pop_area_level = serializers.SerializerMethodField(read_only=True)
    pop_statistics_area_level = serializers.SerializerMethodField(read_only=True)
    default_demand_rate_sets = serializers.SerializerMethodField(read_only=True)
    default_mode_variants = serializers.SerializerMethodField(read_only=True)
    default_prognosis = serializers.SerializerMethodField(read_only=True)

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
