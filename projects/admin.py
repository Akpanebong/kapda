from django.contrib import admin
from .models import ActivityData, Indicator, MonitoringForm, Project
from .forms import MonitoringFormDefinitionForm


@admin.register(MonitoringForm)
class MonitoringFormAdmin(admin.ModelAdmin):
    form = MonitoringFormDefinitionForm
    list_display = ("indicator", "is_active", "updated_at")
    list_filter = ("is_active",)


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "project", 'status')


admin.site.register([Project, ActivityData])
