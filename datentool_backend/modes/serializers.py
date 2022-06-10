from rest_framework import serializers

from .models import ModeVariant, Network


class ModeVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeVariant
        fields = ('id', 'mode', 'cutoff_time')


class NetworkSerializer(serializers.ModelSerializer):
    modes = ModeVariantSerializer(many=True, read_only=True)
    class Meta:
        model = Network
        fields = ('id', 'name', 'modes', 'is_default')
