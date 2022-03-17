from rest_framework import serializers
from .models import SiteSetting, ProjectSetting, BaseDataSetting, AreaLevel
from datentool_backend.utils.geometry_fields import MultiPolygonGeometrySRIDField
from datentool_backend.models import DemandRateSet, Prognosis, ModeVariant


class ProjectSettingSerializer(serializers.ModelSerializer):
    project_area = MultiPolygonGeometrySRIDField(srid=3857)

    class Meta:
        model = ProjectSetting
        fields = ('project_area', 'start_year', 'end_year')


class BaseDataSettingSerializer(serializers.ModelSerializer):
    pop_statistics_area_level = serializers.SerializerMethodField(read_only=True)
    default_demand_rate_sets = serializers.SerializerMethodField(read_only=True)
    default_mode_variants = serializers.SerializerMethodField(read_only=True)
    default_prognosis = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BaseDataSetting
        fields = ('default_pop_area_level', 'pop_statistics_area_level',
                  'default_demand_rate_sets', 'default_mode_variants',
                  'default_prognosis')

    # ToDo: what in case get returns multiple objects?
    # (is the case for all default functions here, but should already be
    # prevented in model)
    def get_pop_statistics_area_level(self, obj):
        try:
            level = AreaLevel.objects.get(is_statistic_level=True)
            return level.id
        except AreaLevel.DoesNotExist:
            return

    def get_default_demand_rate_sets(self, obj):
        sets = DemandRateSet.objects.filter(
            is_default=True).order_by('service_id')
        return dict(sets.values_list('service_id', 'id'))

    def get_default_mode_variants(self, obj):
        sets = ModeVariant.objects.filter(is_default=True).order_by('mode')
        return dict(sets.values_list('mode', 'id'))

    def get_default_prognosis(self, obj):
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
                  'primary_color', 'secondary_color', 'welcome_text')
