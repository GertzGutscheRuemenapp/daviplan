from django.contrib import admin

from .models.places import (
    Place,
    Capacity,
    PlaceField
)
from .models.process_scenario import PlanningProcess, Scenario

admin.site.register(Place)
admin.site.register(Capacity)
admin.site.register(PlaceField)
admin.site.register(PlanningProcess)
admin.site.register(Scenario)
