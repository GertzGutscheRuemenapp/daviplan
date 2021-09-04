from rest_framework import serializers

from .models import SymbolForm, MapSymbols


class SymbolFormSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SymbolForm
        fields =  ('id', 'name', )


class MapSymbolsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapSymbols
        fields =  ('id', 'symbol', 'fill_color', 'stroke_color')

