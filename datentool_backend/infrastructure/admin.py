from django.contrib import admin
from .models.infrastructures import (
    Service, Infrastructure
)
from .models.places import (
    Place,
    Capacity,
    PlaceField
)

admin.site.register(Infrastructure)
admin.site.register(Service)
admin.site.register(Place)
admin.site.register(Capacity)
admin.site.register(PlaceField)
