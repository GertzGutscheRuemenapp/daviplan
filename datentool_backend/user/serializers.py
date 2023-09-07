from django.contrib.auth.models import User
from rest_framework import serializers
from django.conf import settings

from datentool_backend.user.models import Profile
from datentool_backend.infrastructure.models import InfrastructureAccess


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        if getattr(settings, 'DEMO_MODE'):
            user = User.objects.get(
                **{self.username_field: attrs[self.username_field]})
            # skip password authentication for demo user in demo mode
            if (user.profile.is_demo_user):
                self.user = user
                refresh = self.get_token(self.user)
                return {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
        return super().validate(attrs)


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = ('admin_access', 'can_create_process', 'can_edit_basedata',
                  'is_demo_user')


class UserAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureAccess
        fields = ('infrastructure', 'allow_sensitive_data')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    profile = ProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=False)
    access = UserAccessSerializer(
        many=True, source='profile.infrastructureaccess_set', required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'access',
                  'last_name', 'is_superuser', 'profile', 'password')

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        instance = super().create(validated_data)
        if password:
            instance.set_password(password)
        instance.save()
        profile = instance.profile
        for k, v in profile_data.items():
            setattr(profile, k, v)
        profile.save()
        return instance

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        access = profile_data.pop('infrastructureaccess_set', None)
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        profile = instance.profile
        for k, v in profile_data.items():
            setattr(profile, k, v)
        profile.save()
        if access is not None:
            InfrastructureAccess.objects.filter(profile=profile).delete()
            for ia in access:
                infra_access = InfrastructureAccess(
                    infrastructure=ia['infrastructure'],
                    allow_sensitive_data=ia.get(
                        'allow_sensitive_data', False),
                    profile=profile)
                infra_access.save()
        return super().update(instance, validated_data)
