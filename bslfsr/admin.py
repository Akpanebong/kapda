from django.contrib import admin
from .models import Beneficiary, FarmerRecord, PeaceActivity, PeaceCommittee

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display=("beneficiary_id","full_name","participant_category","displacement_status","sex","project","active")
    search_fields=("beneficiary_id","full_name","phone")
    list_filter=("participant_category","displacement_status","sex","disability_status","active","project")

admin.site.register([FarmerRecord, PeaceActivity, PeaceCommittee])
