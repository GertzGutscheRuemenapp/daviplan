from rest_framework import serializers

from datentool_backend.infrastructure.models.infrastructures import (
    InfrastructureAccess, Infrastructure)
from datentool_backend.area.models import MapSymbol
from datentool_backend.area.serializers import MapSymbolSerializer
from datentool_backend.infrastructure.serializers import PlaceFieldInfraSerializer

class InfrastructureAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureAccess
        fields = ('infrastructure', 'profile', 'allow_sensitive_data')
        read_only_fields = ('id', 'infrastructure', )


class InfrastructureSerializer(serializers.ModelSerializer):
    symbol = MapSymbolSerializer(allow_null=True, required=False)
    accessible_by = InfrastructureAccessSerializer(
        many=True, source='infrastructureaccess_set', required=False)
    place_fields = PlaceFieldInfraSerializer(many=True, source='placefield_set',
                                             required=False, read_only=True)
    places_count = serializers.SerializerMethodField()

    class Meta:
        model = Infrastructure
        fields = ('id', 'name', 'description',
                  'editable_by', 'accessible_by',
                  'order', 'symbol', 'place_fields', 'places_count')
        extra_kwargs = {'description': {'required':  False}}
        #read_only_fields = (place_fields, )

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
            infrastructure_access.allow_sensitive_data = profile_access[
                'allow_sensitive_data']
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
                infrastructure_access.allow_sensitive_data = profile_access[
                    'allow_sensitive_data']
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

    def get_places_count(self, instance):
        return instance.place_set.count()

