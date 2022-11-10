from rest_framework import serializers

from .models import ModeVariant, Network


class ModeVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeVariant
        fields = ('id', 'mode', 'network', 'label', 'is_default', 'cutoff_time')
        read_only_fields = ('cutoff_time', )


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Network
        fields = ('id', 'name', 'is_default')
