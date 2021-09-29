from django.contrib import admin
from .models import (
    CapacityUploadLog, AreaUploadLog, PlaceUploadLog)

# Register your models here.
class CapacityUploadLogAdmin(admin.ModelAdmin):
    """"""


class AreaUploadLogAdmin(admin.ModelAdmin):
    """"""


class PlaceUploadLogAdmin(admin.ModelAdmin):
    """"""


admin.site.register(CapacityUploadLog, CapacityUploadLogAdmin)
admin.site.register(AreaUploadLog, AreaUploadLogAdmin)
admin.site.register(PlaceUploadLog, PlaceUploadLogAdmin)
