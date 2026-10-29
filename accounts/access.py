from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .models import User


def is_system_administrator(user):
    """Return whether the user may manage staff accounts and system settings."""
    return user.is_authenticated and (user.is_superuser or user.role == User.Role.ADMIN)


def can_edit_records(user):
    """Operational staff may maintain programme records; viewers are read-only."""
    editable_roles = {
        User.Role.ADMIN,
        User.Role.TEACHER,
        User.Role.DATA_ENTRY,
        User.Role.MEAL,
        User.Role.MANAGER,
    }
    return user.is_authenticated and user.is_active and (
        user.is_superuser or user.role in editable_roles
    )


def system_admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if not is_system_administrator(request.user):
            return HttpResponseForbidden("Only system administrators may create, update, or delete records.")
        return view_func(request, *args, **kwargs)
    return wrapped


def record_editor_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if not can_edit_records(request.user):
            return HttpResponseForbidden("Your account is read-only and cannot create, update, or delete records.")
        return view_func(request, *args, **kwargs)
    return wrapped
