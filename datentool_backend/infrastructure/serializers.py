from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (Infrastructure, FieldType, FClass, FieldTypes, Service,
                     Place, Capacity, PlaceField, ScenarioPlace,
                     InternalWFSLayer, ScenarioCapacity, InfrastructureAccess)
from datentool_backend.area.serializers import InternalWFSLayerSerializer
from datentool_backend.area.models import LayerGroup, MapSymbol


class InfrastructureAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureAccess
        fields = ('id', 'infrastructure', 'profile', 'allow_sensitive_data')
        read_only_fields = ('id', 'infrastructure', )


class InfrastructureSerializer(serializers.ModelSerializer):
    layer = InternalWFSLayerSerializer(allow_null=True)
    layer_group = 'Infrastruktur-Standorte'
    accessible_by = InfrastructureAccessSerializer(many=True,
                                                   source='infrastructureaccess_set')

    class Meta:
        model = Infrastructure
        fields = ('id', 'name', 'description',
                  'editable_by', 'accessible_by',
                  'layer')

    def create(self, validated_data):
        layer_data = validated_data.pop('layer', {})
        symbol_data = layer_data.pop('symbol', {})
        symbol = MapSymbol.objects.create(**symbol_data)

        group, created = LayerGroup.objects.get_or_create(
            name=self.layer_group, external=False)
        l_name = layer_data.pop('name', validated_data['name'])
        l_layer_name = layer_data.pop('layer_name', validated_data['name'])
        existing = Infrastructure.objects.all().order_by('layer__order')
        order = layer_data.pop('order', existing.last().layer.order + 1)
        layer = InternalWFSLayer.objects.create(
            symbol=symbol, name=l_name, layer_name=l_layer_name, order=order,
            group=group, active=True, **layer_data)

        editable_by = validated_data.pop('editable_by', [])
        accessible_by = validated_data.pop('infrastructureaccess_set', [])
        infrastructure = Infrastructure.objects.create(layer=layer,
                                                       **validated_data)
        infrastructure.editable_by.set(editable_by)
        infrastructure.accessible_by.set([a['profile'] for a in accessible_by])
        for profile_access in accessible_by:
            infrastructure_access = InfrastructureAccess.objects.get(
                infrastructure=infrastructure,
                profile=profile_access['profile'])
            infrastructure_access.allow_sensitive_data = profile_access['allow_sensitive_data']
            infrastructure_access.save()

        return infrastructure

    def update(self, instance, validated_data):
        layer_data = validated_data.pop('layer', {})
        symbol_data = layer_data.pop('symbol', {})

        editable_by = validated_data.pop('editable_by', None)
        accessible_by = validated_data.pop('infrastructureaccess_set', None)
        super().update(instance, validated_data)
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
        instance.save()

        layer = instance.layer
        layer.name = layer_data.get('name', layer.name)
        layer.layer_name = layer_data.get('layer_name', layer.layer_name)
        layer.order = layer_data.get('order', layer.order)
        layer.save()

        symbol = layer.symbol
        symbol.symbol = symbol_data.get('symbol', symbol.symbol)
        symbol.fill_color = symbol_data.get('fill_color', symbol.fill_color)
        symbol.stroke_color = symbol_data.get('stroke_color',
                                              symbol.stroke_color)
        symbol.save()

        return instance


class ServiceSerializer(serializers.ModelSerializer):
    #quota_id = serializers.IntegerField(write_only=True, source='quota')
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'infrastructure', 'editable_by',
                  'capacity_singular_unit', 'capacity_plural_unit',
                  'has_capacity', 'demand_singular_unit', 'demand_plural_unit',
                  'quota_type')


class PlaceSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Place
        geo_field = 'geom'
        fields = ('id', 'name', 'infrastructure', 'attributes')


class ScenarioPlaceSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = ScenarioPlace
        geo_field = 'geom'
        fields = ('id', 'name', 'infrastructure', 'attributes', "scenario",
                  "status_quo")


class CapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Capacity
        fields = ('id', 'place', 'service', 'capacity', 'from_year')


class ScenarioCapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioCapacity
        fields = ('id', 'place', 'service', 'capacity', 'from_year', "scenario",
                  "status_quo")


class FClassSerializer(serializers.ModelSerializer):
    classification_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        source='classification',
        queryset = FieldType.objects.all())

    class Meta:
        model = FClass
        read_only_fields = ('id', 'classification', )
        write_only_fields = ('classification_id', )
        fields = ('id', 'order', 'value',
                  'classification', 'classification_id')


class FieldTypeSerializer(serializers.ModelSerializer):

    classification = FClassSerializer(required=False, many=True,
                                      source='fclass_set')

    class Meta:
        model = FieldType
        fields = ('id', 'name', 'field_type', 'classification')

    def create(self, validated_data):
        classification_data = validated_data.pop('fclass_set', {})
        instance = super().create(validated_data)
        instance.save()
        if classification_data and instance.field_type == FieldTypes.CLASSIFICATION:
            for classification in classification_data:
                fclass = FClass(order=classification['order'],
                                classification=instance,
                                value=classification['value'])
                fclass.save()
        return instance

    def update(self, instance, validated_data):
        classification_data = validated_data.pop('fclass_set', {})
        instance = super().update(instance, validated_data)
        if classification_data and instance.field_type == FieldTypes.CLASSIFICATION:
            classification_list = []
            for classification in classification_data:
                fclass = FClass(order=classification['order'],
                                classification=instance,
                                value=classification['value'])
                fclass.save()
                classification_list.append(fclass)
            classification_data_ids = [f.id for f in classification_list]
            for fclass in instance.fclass_set.all():
                if fclass.id not in classification_data_ids:
                    fclass.delete(keep_parents=True)
        return instance


class PlaceFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceField
        fields = ('id', 'attribute', 'unit', 'infrastructure',
                  'field_type', 'sensitive')
