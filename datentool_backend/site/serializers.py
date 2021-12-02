from rest_framework import serializers

from .models import SiteSetting, ProjectSetting


class ProjectSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSetting
        fields = ('project_area', 'start_year', 'end_year')


class SiteSettingSerializer(serializers.HyperlinkedModelSerializer):
    ''''''
    url = serializers.HyperlinkedIdentityField(
        view_name='settings-detail', read_only=True)

    class Meta:
        model = SiteSetting
        fields = ('id', 'url', 'name', 'title', 'contact_mail', 'logo',
                  'primary_color', 'secondary_color', 'welcome_text')
