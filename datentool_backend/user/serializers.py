from rest_framework import serializers
from django.contrib.auth.models import User
import json

from .models import (Profile,
                     Year,
                     PlanningProcess,
                     Infrastructure,
                     InfrastructureAccess,
                     Service,
                     )

from datentool_backend.area.models import MapSymbol
from datentool_backend.area.serializers import MapSymbolSerializer

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
    class Meta:
        model = Year
        fields = ('id', 'year')


class PlanningProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanningProcess
        fields = ('id', 'name', 'owner', 'users', 'allow_shared_change')


class InfrastructureAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureAccess
        fields = ('infrastructure', 'profile', 'allow_sensitive_data')
        read_only_fields = ('id', 'infrastructure', )


class InfrastructureSerializer(serializers.ModelSerializer):
    symbol = MapSymbolSerializer(allow_null=True, required=False)
    accessible_by = InfrastructureAccessSerializer(
        many=True, source='infrastructureaccess_set', required=False)

    class Meta:
        model = Infrastructure
        fields = ('id', 'name', 'description',
                  'editable_by', 'accessible_by',
                  'order', 'symbol')

    def create(self, validated_data):
        symbol_data = validated_data.pop('symbol', None)
        symbol = MapSymbol.objects.create(**symbol_data) \
            if symbol_data else None

        editable_by = validated_data.pop('editable_by', [])
        accessible_by = validated_data.pop('infrastructureaccess_set', [])
        instance = Infrastructure.objects.create(
            symbol=symbol, **validated_data)
        instance.editable_by.set(editable_by)
        instance.accessible_by.set([a['profile'] for a in accessible_by])
        for profile_access in accessible_by:
            infrastructure_access = InfrastructureAccess.objects.get(
                infrastructure=instance,
                profile=profile_access['profile'])
            infrastructure_access.allow_sensitive_data = profile_access['allow_sensitive_data']
            infrastructure_access.save()

        return instance

    def update(self, instance, validated_data):
        # symbol is nullable
        update_symbol = 'symbol' in validated_data
        symbol_data = validated_data.pop('symbol', None)

        editable_by = validated_data.pop('editable_by', None)
        accessible_by = validated_data.pop('infrastructureaccess_set', None)
        instance = super().update(instance, validated_data)
        if editable_by is not None:
            instance.editable_by.set(editable_by)
        if accessible_by is not None:
            instance.accessible_by.set([a['profile'] for a in accessible_by])
            for profile_access in accessible_by:
                infrastructure_access = InfrastructureAccess.objects.get(
                    infrastructure=instance,
                    profile=profile_access['profile'])
                infrastructure_access.allow_sensitive_data = profile_access['allow_sensitive_data']
                infrastructure_access.save()

        if update_symbol:
            symbol = instance.symbol
            if symbol_data:
                if not symbol:
                    symbol = MapSymbol.objects.create(**symbol_data)
                    instance.symbol = symbol
                else:
                    for k, v in symbol_data.items():
                        setattr(symbol, k, v)
                    symbol.save()
            # symbol passed but is None -> intention to set it to null
            else:
                symbol.delete()
                instance.symbol = None

        instance.save()
        return instance


class ServiceSerializer(serializers.ModelSerializer):
    #quota_id = serializers.IntegerField(write_only=True, source='quota')
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'infrastructure', 'editable_by',
                  'capacity_singular_unit', 'capacity_plural_unit',
                  'has_capacity', 'demand_singular_unit', 'demand_plural_unit',
                  'quota_type', 'demand_name', 'demand_description')


