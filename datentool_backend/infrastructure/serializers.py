from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (Infrastructure, FieldType, FClass, FieldTypes, Service,
                     Quota, Place, Capacity, PlaceField)


class InfrastructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Infrastructure
        fields = ('id', 'name', 'description',
                   'editable_by', 'accessible_by',
                   'layer', 'symbol')


class QuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quota
        fields = ('id', 'quota_type')


class ServiceSerializer(serializers.ModelSerializer):
    quota_type = QuotaSerializer(read_only=True, source='quota')
    quota_id = serializers.IntegerField(write_only=True, source='quota')
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'infrastructure', 'editable_by',
                  'capacity_singular_unit', 'capacity_plural_unit',
                  'has_capacity', 'demand_singular_unit', 'demand_plural_unit',
                  'quota_id', 'quota_type')

    def create(self, validated_data):
        quota_id = validated_data.pop('quota')
        quota = Quota.objects.get(pk=quota_id)
        validated_data['quota'] = quota
        instance = super().create(validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        quota_id = validated_data.pop('quota')
        if quota_id is not None:
            quota = Quota.objects.get(pk=quota_id)
            validated_data['quota'] = quota
        instance = super().update(instance, validated_data)
        return instance


class PlaceSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Place
        geo_field = 'geom'
        fields = ('id', 'name', 'infrastructure', 'attributes')


class CapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Capacity
        fields = ('id', 'place', 'service', 'capacity', 'from_year')


class FClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = FClass
        fields = ('id', 'order', 'value')


class FieldTypeSerializer(serializers.ModelSerializer):

    fclass_set = FClassSerializer(required=False, many=True)

    class Meta:
        model = FieldType
        fields = ('id', 'name', 'field_type', 'fclass_set')

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
            for classification in classification_data:
                if classification.get('id') is None:
                    fclass = FClass(order=classification['order'],
                                    classification=instance,
                                    value=classification['value'])
                    fclass.save()
                else:
                    try:
                        fclass = FClass.objects.get(id=classification['id'],
                                                    classification=instance)
                        fclass.order = classification['order']
                        fclass.value = classification['value']
                        fclass.save()
                    except FClass.DoesNotExist:
                        print(f'FClass with id {id} in field-type '
                              '{instance.name} does not exist')
            classification_data_ids = [f['id'] for f in classification_data]
            for fclass in instance.fclass_set:
                if fclass.id not in classification_data_ids:
                    fclass.delete(keep_parents=True)
        return instance


class PlaceFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceField
        fields = ('id', 'attribute', 'unit', 'infrastructure', 'field_type')
