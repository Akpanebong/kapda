from django.urls import path, reverse_lazy
from django.contrib.auth.views import (
    LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from .views import KAPDALoginView, account_credentials, staff_list, staff_create, staff_update
app_name = "accounts"
urlpatterns = [path("login/", KAPDALoginView.as_view(), name="login"), path("logout/", LogoutView.as_view(), name="logout"), path("account/credentials/", account_credentials, name="account_credentials"), path("staff/", staff_list, name="staff_list"), path("staff/add/", staff_create, name="staff_create"), path("staff/<int:pk>/edit/", staff_update, name="staff_update")]
urlpatterns += [
    path("password-reset/", PasswordResetView.as_view(
        template_name="accounts/password_reset_form.html",
        email_template_name="accounts/password_reset_email.txt",
        subject_template_name="accounts/password_reset_subject.txt",
        success_url=reverse_lazy("accounts:password_reset_done"),
    ), name="password_reset"),
    path("password-reset/done/", PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html",
    ), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url=reverse_lazy("accounts:password_reset_complete"),
    ), name="password_reset_confirm"),
    path("reset/done/", PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html",
    ), name="password_reset_complete"),
]
