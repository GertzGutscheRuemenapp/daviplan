from django.contrib import admin
from .models import (
    Infrastructure, Quota, Service, Place,
    Capacity, FieldType, FClass, PlaceField)

# Register your models here.
class InfrastructureAdmin(admin.ModelAdmin):
    """"""


class QuotaAdmin(admin.ModelAdmin):
    """"""


class ServiceAdmin(admin.ModelAdmin):
    """"""


class PlaceAdmin(admin.ModelAdmin):
    """"""


class CapacityAdmin(admin.ModelAdmin):
    """"""


class FieldTypeAdmin(admin.ModelAdmin):
    """"""


class FClassAdmin(admin.ModelAdmin):
    """"""


class PlaceFieldAdmin(admin.ModelAdmin):
    """"""


admin.site.register(Infrastructure, InfrastructureAdmin)
admin.site.register(Quota, QuotaAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Place, PlaceAdmin)
admin.site.register(Capacity, CapacityAdmin)
admin.site.register(FieldType, FieldTypeAdmin)
admin.site.register(FClass, FClassAdmin)
admin.site.register(PlaceField, PlaceFieldAdmin)
