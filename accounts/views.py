from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CredentialResetForm, LoginForm, StaffForm
from .models import User
from .access import system_admin_required
class KAPDALoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm


@system_admin_required
def staff_list(request):
    return render(request, "accounts/staff_list.html", {"staff": User.objects.filter(is_staff=True).order_by("last_name", "first_name", "username")})


@system_admin_required
def staff_create(request):
    form = StaffForm(request.POST or None, request.FILES or None, creating=True)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        messages.success(request, f"Staff account created. Username: {user.username}; temporary password: {form.cleaned_data['password']}. The staff member can change it using Forgot password.")
        return redirect("accounts:staff_list")
    return render(request, "accounts/staff_form.html", {"form": form, "creating": True})


@system_admin_required
def staff_update(request, pk):
    user = get_object_or_404(User, pk=pk, is_staff=True)
    form = StaffForm(request.POST or None, request.FILES or None, instance=user, creating=False)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Staff account updated successfully.")
        return redirect("accounts:staff_list")
    return render(request, "accounts/staff_form.html", {"form": form, "creating": False, "staff_user": user})


@login_required
def account_credentials(request):
    form = CredentialResetForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        user = request.user
        user.username = form.cleaned_data["username"]
        user.set_password(form.cleaned_data["new_password1"])
        user.must_change_password = False
        user.save(update_fields=["username", "password", "must_change_password"])
        update_session_auth_hash(request, user)
        messages.success(request, f"Your username and password were updated. Your staff ID remains {user.reg_no}.")
        return redirect("accounts:account_credentials")
    return render(request, "accounts/account_credentials.html", {"form": form})
