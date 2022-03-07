from rest_framework import serializers

from .models import ModeVariant


class ModeVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeVariant
        fields = ('id', 'mode', 'name', 'meta', 'is_default')
