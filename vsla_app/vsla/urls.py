from django.urls import path
from . import views

app_name = "vsla"

urlpatterns = [
    path("", views.dashboard, name="vsla_dashboard"),
    path("groups/", views.group_list, name="groups"),
    path("groups/new/", views.group_create, name="group_create"),
    path("groups/<slug:slug>/meetings/new/", views.meeting_create, name="group_meeting_create"),
    path("groups/<slug:slug>/attendance/", views.attendance_group_list, name="group_attendance"),
    path("groups/<slug:slug>/attendance/<pk_slug:meeting_id>/", views.attendance_detail, name="attendance_detail"),
    path("groups/<slug:slug>/attendance/new/", views.attendance_create, name="group_attendance_create"),
    path("groups/<slug:slug>/", views.group_detail, name="group_detail"),
    path("members/", views.member_list, name="members"),
    path("members/new/", views.member_create, name="member_create"),
    path("members/<pk_slug:member_no>/", views.member_detail, name="member_detail"),
    path("savings/", views.savings_list, name="savings"),
    path("savings/new/", views.savings_create, name="savings_create"),
    path("loans/", views.loan_list, name="loans"),
    path("loans/new/", views.loan_create, name="loan_create"),
    path("loans/<pk_slug:loan_no>/", views.loan_detail, name="loan_detail"),
    path("loans/<pk_slug:loan_no>/submit/", views.loan_submit, name="loan_submit"),
    path("loans/<pk_slug:loan_no>/decision/", views.loan_decision, name="loan_decision"),
    path("loans/<pk_slug:loan_no>/repay/", views.repayment_create, name="repayment_create"),
    path("meetings/", views.meeting_list, name="meetings"),
    path("meetings/new/", views.meeting_create, name="meeting_create"),
    path("attendance/", views.attendance_list, name="attendance"),
    path("attendance/new/", views.attendance_create, name="attendance_create"),
    path("social-fund/", views.social_fund_list, name="social_fund"),
    path("social-fund/new/", views.social_fund_create, name="social_fund_create"),
    path("export/<slug:resource>.csv", views.export_csv, name="export_csv"),
    path("export/<slug:resource>.xlsx", views.export_xlsx, name="export_xlsx"),
    path("export-workbook.xlsx", views.export_workbook, name="export_workbook"),
]
