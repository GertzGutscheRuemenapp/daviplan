from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (Infrastructure, FieldType, FClass, FieldTypes, Service,
                     Place, Capacity, PlaceField)


class InfrastructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Infrastructure
        fields = ('id', 'name', 'description',
                   'editable_by', 'accessible_by',
                   'layer', 'symbol')


class ServiceSerializer(serializers.ModelSerializer):
    #quota_id = serializers.IntegerField(write_only=True, source='quota')
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'infrastructure', 'editable_by',
                  'capacity_singular_unit', 'capacity_plural_unit',
                  'has_capacity', 'demand_singular_unit', 'demand_plural_unit',
                  #'quota_id',
                  'quota_type')


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
                classification_list.append(fclass)
            classification_data_ids = [f.id for f in classification_list]
            for fclass in instance.fclass_set.all():
                if fclass.id not in classification_data_ids:
                    fclass.delete(keep_parents=True)
        return instance


class PlaceFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceField
        fields = ('id', 'attribute', 'unit', 'infrastructure', 'field_type')
