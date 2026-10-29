from django.contrib import admin
from .models import Learner, LearnerProject, Enrolment, ClassMovement, AttendanceRecord, Assessment, UNEBResult, LearnerSupport, LearnerStatusHistory, LearnerEmployment

@admin.register(Learner)
class LearnerAdmin(admin.ModelAdmin):
    list_display=("reg_no","first_name","last_name","participant_category","displacement_status","current_class","status")
    search_fields=("reg_no","first_name","last_name","guardian_phone")
    list_filter=("sex","participant_category","displacement_status","current_class","status","disability_status")


@admin.register(Enrolment)
class EnrolmentAdmin(admin.ModelAdmin):
    list_display=("learner","school","academic_year","outcome")
    search_fields=("learner__first_name","learner__last_name")

for model in [LearnerProject,ClassMovement,AttendanceRecord,Assessment,UNEBResult,LearnerSupport,LearnerStatusHistory,LearnerEmployment]:
    admin.site.register(model)
