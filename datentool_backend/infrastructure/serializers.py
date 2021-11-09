from rest_framework import serializers

from .models import Infrastructure, FieldType, FClass, FieldTypes


class InfrastructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Infrastructure
        fields = ('id', 'name', 'description',
                   'editable_by', 'accessible_by',
                   'layer', 'symbol')


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
