from rest_framework import serializers

from .models import (Mode)


class ModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mode
        fields = ('id', 'name')
