from django.contrib import admin
from .models import (
    SiteSetting)

# Register your models here.
class SiteSettingAdmin(admin.ModelAdmin):
    """"""


admin.site.register(SiteSetting, SiteSettingAdmin)
