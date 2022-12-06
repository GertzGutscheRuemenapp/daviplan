from rest_framework import serializers
from django.db.utils import IntegrityError
from rest_framework.exceptions import NotAcceptable

from datentool_backend.infrastructure.models.infrastructures import (
    InfrastructureAccess, Infrastructure, PlaceField)
from datentool_backend.area.models import MapSymbol, FieldTypes, FieldType
from datentool_backend.area.serializers import MapSymbolSerializer
from datentool_backend.infrastructure.serializers import (
    PlaceFieldNestedSerializer, ADDRESS_FIELDS)


class InfrastructureAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureAccess
        fields = ('infrastructure', 'profile', 'allow_sensitive_data')
        read_only_fields = ('id', 'infrastructure', )


class InfrastructureSerializer(serializers.ModelSerializer):
    symbol = MapSymbolSerializer(allow_null=True, required=False)
    accessible_by = InfrastructureAccessSerializer(
        many=True, source='infrastructureaccess_set', required=False)
    place_fields = PlaceFieldNestedSerializer(
        many=True, source='placefield_set', required=False)
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

        # preset fields for address uploads
        str_type = FieldType.objects.get(ftype=FieldTypes.STRING)
        for field_name in ADDRESS_FIELDS.keys():
            PlaceField.objects.create(infrastructure=instance, name=field_name,
                                      is_preset=True, field_type=str_type)

        for profile_access in accessible_by:
            infrastructure_access = InfrastructureAccess.objects.get(
                infrastructure=instance,
                profile=profile_access['profile'])
            infrastructure_access.allow_sensitive_data = profile_access[
                'allow_sensitive_data']
            infrastructure_access.save()

        placefield_data = validated_data.pop('placefield_set', None)
        if placefield_data is not None:
            self._update_placefields(instance, placefield_data)

        return instance

    def update(self, instance, validated_data):
        # symbol is nullable
        update_symbol = 'symbol' in validated_data
        symbol_data = validated_data.pop('symbol', None)
        placefield_data = validated_data.pop('placefield_set', None)
        editable_by = validated_data.pop('editable_by', None)
        accessible_by = validated_data.pop('infrastructureaccess_set', None)

        instance = super().update(instance, validated_data)

        if placefield_data is not None:
            self._update_placefields(instance, placefield_data)
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

    def _update_placefields(self, instance, data):
        place_fields = []
        names = [f['name'] for f in data]
        if (len(set(names)) != len(names)):
            raise NotAcceptable('Die Kurznamen der Attribute müssen einzigartig sein!')
        # '_' is not allowed because of serializer which is auto camel-casing it
        for name in names:
            if '_' in name:
                raise NotAcceptable('Die Kurznamen der Attribute dürfen kein "_" enthalten!')
        for pf_data in data:
            pf_id = pf_data.get('id', None)
            field_name = pf_data['name']
            if pf_id is not None:
                place_field = PlaceField.objects.get(id=pf_id)
                place_field.field_type = pf_data['field_type']
                place_field.name = field_name
            else:
                try:
                    place_field = PlaceField.objects.create(
                        infrastructure=instance,
                        name=field_name,
                        field_type=pf_data['field_type']
                    )
                except IntegrityError:
                    raise NotAcceptable(
                        f'Der Name des Feldes "{field_name}" ist '
                        'bereits so oder in anderer Schreibweise vorhanden')
            place_field.unit = pf_data.get('unit', '')
            place_field.label = pf_data.get('label', '')
            place_field.sensitive = pf_data.get('sensitive', False)
            try:
                place_field.save()
            except IntegrityError:
                raise NotAcceptable(
                    f'Der Name des Feldes "{field_name}" ist '
                    'bereits so oder in anderer Schreibweise vorhanden')
            place_fields.append(place_field)
        place_fields_ids = [f.id for f in place_fields]
        for place_field in instance.placefield_set.exclude(
            is_preset=True).exclude(id__in=place_fields_ids):
            place_field.delete(keep_parents=True)

    def get_places_count(self, instance):
        return instance.place_set.count()

