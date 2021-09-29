from rest_framework import serializers

from .models import SiteSetting


class SiteSettingsSerializer(serializers.HyperlinkedModelSerializer):
    ''''''
    url = serializers.HyperlinkedIdentityField(
        view_name='settings-detail', read_only=True)

    class Meta:
        model = SiteSetting
        fields = ('id', 'url', 'name', 'title', 'contact_mail', 'logo',
                  'primary_color', 'secondary_color', 'welcome_text')
