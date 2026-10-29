from django.urls import path
from .views import dashboard, exports, learner_export, learner_export_xlsx, learner_export_pdf, beneficiary_export_xlsx, beneficiary_export_pdf, peacebuilding_export_xlsx, peacebuilding_export_pdf, livelihoods_food_security_peacebuilding_export_xlsx, livelihoods_food_security_peacebuilding_export_pdf

app_name="reports"

urlpatterns=[
    path("",dashboard,name="reports_dashboard"),
    path("exports/",exports,name="exports"),
    path("export/learners.csv",learner_export,name="learner_export"),
    path("export/learners.xlsx",learner_export_xlsx,name="learner_export_xlsx"),
    path("export/learners.pdf",learner_export_pdf,name="learner_export_pdf"),
    path("export/beneficiaries.xlsx",beneficiary_export_xlsx,name="beneficiary_export_xlsx"),
    path("export/beneficiaries.pdf",beneficiary_export_pdf,name="beneficiary_export_pdf"),
    path("export/peacebuilding.xlsx",peacebuilding_export_xlsx,name="peacebuilding_export_xlsx"),
    path("export/peacebuilding.pdf",peacebuilding_export_pdf,name="peacebuilding_export_pdf"),
    path("export/livelihoods-food-security-peacebuilding.xlsx", livelihoods_food_security_peacebuilding_export_xlsx, name="livelihoods_food_security_peacebuilding_export_xlsx"),
    path("export/livelihoods-food-security-peacebuilding.pdf", livelihoods_food_security_peacebuilding_export_pdf, name="livelihoods_food_security_peacebuilding_export_pdf"),
]
