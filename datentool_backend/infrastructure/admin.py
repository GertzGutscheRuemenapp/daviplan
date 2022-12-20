from django.contrib import admin
from .models import (
    Service, Infrastructure
)

admin.site.register(Infrastructure)
admin.site.register(Service)
