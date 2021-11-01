from rest_framework import serializers

from .models import SymbolForm, MapSymbol


class SymbolFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = SymbolForm
        fields =  ('id', 'name', )


class MapSymbolsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapSymbol
        fields =  ('id', 'symbol', 'fill_color', 'stroke_color')

