from django.contrib import admin
from .models import (
    Infrastructure, Service, Place,
    Capacity, FieldType, FClass, PlaceField, ScenarioPlace)

admin.site.register(Infrastructure)
admin.site.register(Service)
admin.site.register(Place)
admin.site.register(Capacity)
admin.site.register(FieldType)
admin.site.register(FClass)
admin.site.register(PlaceField)
admin.site.register(ScenarioPlace)
