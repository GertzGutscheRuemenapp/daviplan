from django.contrib import admin
from .models import (
    Scenario,
    Place,
    Capacity,
    PlaceField,
)

admin.site.register(Scenario)
admin.site.register(Place)
admin.site.register(Capacity)
admin.site.register(PlaceField)
