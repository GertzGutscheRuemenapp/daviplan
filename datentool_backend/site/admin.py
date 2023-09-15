from django.contrib import admin
from .models import (SiteSetting, ProjectSetting)

admin.site.register(ProjectSetting)
admin.site.register(SiteSetting)