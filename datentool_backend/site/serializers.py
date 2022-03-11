from rest_framework import serializers
from .models import SiteSetting, ProjectSetting, BaseDataSetting, AreaLevel
from datentool_backend.utils.geometry_fields import MultiPolygonGeometrySRIDField


class ProjectSettingSerializer(serializers.ModelSerializer):
    project_area = MultiPolygonGeometrySRIDField(srid=3857)

    class Meta:
        model = ProjectSetting
        fields = ('project_area', 'start_year', 'end_year')


class BaseDataSettingSerializer(serializers.ModelSerializer):
    pop_statistics_area_level = serializers.SerializerMethodField()

    class Meta:
        model = BaseDataSetting
        fields = ('default_pop_area_level', 'pop_statistics_area_level')

    def get_pop_statistics_area_level(self, obj):
        try:
            level = AreaLevel.objects.get(is_statistic_level=True)
            return level.id
        except AreaLevel.DoesNotExist:
            return


class SiteSettingSerializer(serializers.ModelSerializer):
    #''''''
    #url = serializers.HyperlinkedIdentityField(
        #view_name='settings-detail', read_only=True)

    class Meta:
        model = SiteSetting
        fields = ('name', 'title', 'contact_mail', 'logo',
                  'primary_color', 'secondary_color', 'welcome_text')
