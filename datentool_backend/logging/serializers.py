from rest_framework import serializers

from .models import (CapacityUploadLog, PlaceUploadLog, AreaUploadLog)


class CapacityUploadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapacityUploadLog
        fields = ('id', 'user', 'date', 'text', 'service')


class PlaceUploadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceUploadLog
        fields = ('id', 'user', 'date', 'text', 'infrastructure')


class AreaUploadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaUploadLog
        fields = ('id', 'user', 'date', 'text', 'level')