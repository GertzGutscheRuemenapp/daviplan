from rest_framework import serializers

from datentool_backend.area.models import MapSymbol, LayerGroup, WMSLayer, Source


class MapSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapSymbol
        fields =  ('symbol', 'fill_color', 'stroke_color')


class LayerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayerGroup
        fields = ('id', 'name', 'order', 'external')


class WMSLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WMSLayer
        fields = ('id', 'name', 'group', 'layer_name', 'order', 'url',
                  'description', 'active')
        optional_fields = ('description', 'active')


class GetCapabilitiesRequestSerializer(serializers.Serializer):
    url = serializers.URLField()
    version = serializers.CharField(required=False, default='1.3.0')


class LayerSerializer(serializers.Serializer):
    name = serializers.CharField()
    title = serializers.CharField()
    abstract = serializers.CharField()
    bbox = serializers.ListField(child=serializers.FloatField(),
                                 min_length=4, max_length=4)


class GetCapabilitiesResponseSerializer(serializers.Serializer):
    version = serializers.CharField()
    url = serializers.URLField()
    cors = serializers.BooleanField()
    layers = LayerSerializer(many=True)


class SourceSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format='%d.%m.%Y',
                                 input_formats=['%d.%m.%Y', 'iso-8601'],
                                 required=False)
    class Meta:
        model = Source
        fields = ('source_type', 'date', 'url', 'layer')
        extra_kwargs = {'url': {'required': False},
                        'layer': {'required': False}}
