from rest_framework import serializers

from .models import LogEntry


class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = ('id', 'user', 'date', 'room', 'text')
