from django.contrib import admin
from .models import (
    CapacityUploadLog, AreaUploadLog, PlaceUploadLog)


admin.site.register(CapacityUploadLog)
admin.site.register(AreaUploadLog)
admin.site.register(PlaceUploadLog)
