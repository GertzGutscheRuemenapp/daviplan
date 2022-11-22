from rest_framework import serializers

from .models import LogEntry


class LogEntrySerializer(serializers.ModelSerializer):
    timestamp = serializers.SerializerMethodField()
    message = serializers.CharField(source='text')
    class Meta:
        model = LogEntry
        fields = ('user', 'level', 'timestamp', 'message', 'room', 'status')

    def get_timestamp(self, obj):
        return obj.date.strftime('%d.%m.%Y %H:%M:%S')
