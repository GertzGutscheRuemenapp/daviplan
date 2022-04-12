import pandas as pd

from django.contrib.auth.models import User
from django.db.models import Min

from rest_framework import serializers

from datentool_backend.user.models.profile import Profile
from datentool_backend.user.models.process import PlanningProcess
from datentool_backend.population.models import Year
from datentool_backend.infrastructure.models.infrastructures import (
    InfrastructureAccess)


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = ('admin_access', 'can_create_process', 'can_edit_basedata')


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


class YearSerializer(serializers.ModelSerializer):
    has_real_data = serializers.BooleanField(source='has_real',
                                             read_only=True)
    has_prognosis_data = serializers.BooleanField(source='has_prognosis',
                                                  read_only=True)
    class Meta:
        model = Year
        fields = ('id', 'year', 'is_prognosis', 'is_real',
                  'has_real_data', 'has_prognosis_data')


class PlanningProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanningProcess
        fields = ('id', 'name', 'owner', 'users', 'allow_shared_change',
                  'description')
        read_only_fields = ('owner', )

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            owner = request.user.profile
            validated_data['owner'] = owner
            return super().create(validated_data)
        else:
            raise serializers.ValidationError('user could not be determined')
