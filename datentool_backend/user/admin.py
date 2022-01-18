from django.contrib import admin
from .models import (
    Profile, PlanningProcess, Scenario)

# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    """"""


class PlanningProcessAdmin(admin.ModelAdmin):
    """"""


class ScenarioAdmin(admin.ModelAdmin):
    """"""

admin.site.register(Profile, ProfileAdmin)
admin.site.register(PlanningProcess, PlanningProcessAdmin)
admin.site.register(Scenario, ScenarioAdmin)
