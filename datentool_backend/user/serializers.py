from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Profile


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    class Meta:
        model = Profile
        fields =  ('admin_access', 'can_create_scenarios', 'can_edit_data')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    profile = ProfileSerializer(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail', read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'is_superuser', 'profile', 'url', 'password')
        #extra_kwargs = {'profile': {'required': False, 'allow_null': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance = super().create(validated_data)
        profile = instance.profile
        for k, v in profile_data.items():
            setattr(profile, k, v)
        profile.save()
        return instance

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        profile = instance.profile
        for k, v in profile_data.items():
            setattr(profile, k, v)
        profile.save()
        return super().update(instance, validated_data)




