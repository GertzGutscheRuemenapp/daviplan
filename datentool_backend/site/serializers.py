from rest_framework import serializers

from .models import SiteSetting, ProjectSetting, BaseDataSetting


class ProjectSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSetting
        fields = ('project_area', 'start_year', 'end_year')


class BaseDataSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDataSetting
        fields = ('default_pop_area_level', )


class SiteSettingSerializer(serializers.HyperlinkedModelSerializer):
    ''''''
    url = serializers.HyperlinkedIdentityField(
        view_name='settings-detail', read_only=True)

    class Meta:
        model = SiteSetting
        fields = ('id', 'url', 'name', 'title', 'contact_mail', 'logo',
                  'primary_color', 'secondary_color', 'welcome_text')
