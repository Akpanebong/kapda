from django.contrib import admin
from .models import Household, FieldAttendance


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("household_id", "household_head", "location", "active")
    search_fields = ("household_id", "household_head")
    list_filter = (("active",))


@admin.register( FieldAttendance)
class FieldAttendanceAdmin(admin.ModelAdmin):
    list_display = ("district", "activity", "submitted_by", "created_at")

