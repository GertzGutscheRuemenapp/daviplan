from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from datentool_backend.utils.geometry_fields import MultiPolygonGeometrySRIDField

from datentool_backend.area.models import Area, AreaAttribute, AreaField


class AreaAttributeField(serializers.JSONField):

    def get_attribute(self, instance):
        return instance

    def to_representation(self, value):
        data = {}
        for field_name in value.field_names.strip("'").split(','):
            try:
                field_value = getattr(value, field_name)
            except AttributeError:
                try:
                    field_value = AreaAttribute.objects\
                        .get(area=value, field__name=field_name)\
                        .value
                except AreaAttribute.DoesNotExist:
                    field_value = ''
            data[field_name] = field_value
        return data


class AreaSerializer(GeoFeatureModelSerializer):
    geom = MultiPolygonGeometrySRIDField(srid=3857)
    attributes = AreaAttributeField(source='areaattribute_set')
    label = serializers.SerializerMethodField()
    key = serializers.SerializerMethodField()

    class Meta:
        model = Area
        geo_field = 'geom'
        fields = ('id', 'area_level', 'attributes', 'label', 'key')

    def get_label(self, obj: Area) -> str:
        return obj.label

    def get_key(self, obj: Area) -> str:
        return obj.key

    def create(self, validated_data):
        """
        Create and return a new `Area` instance, given the validated data.
        """
        attributes = validated_data.pop('areaattribute_set')
        area = super().create(validated_data)

        for field_name, value in attributes.items():
            field = AreaField.objects.get(area_level=area.area_level,
                                          name=field_name)
            AreaAttribute.objects.create(area=area,
                                         field=field,
                                         value=value)
        return area

    def update(self, instance, validated_data):
        """
        Update an Area instance, given the validated data.
        """
        attributes = validated_data.pop('areaattribute_set')
        area = super().update(instance, validated_data)

        existing_area_attributes = AreaAttribute.objects.filter(area=area)
        existing_area_attributes.delete()

        for field_name, value in attributes.items():
            field = AreaField.objects.get(area_level=area.area_level,
                                          name=field_name)
            AreaAttribute.objects.create(area=area,
                                         field=field,
                                         value=value)
        return instance
