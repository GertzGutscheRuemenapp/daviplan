from django.contrib import admin
from .models import (Profile, Year, PlanningProcess, Scenario)

# Register your models here.

# Register your models here.
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """"""


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    """"""


@admin.register(PlanningProcess)
class PlanningProcessAdmin(admin.ModelAdmin):
    """"""


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    """"""
