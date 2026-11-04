from functools import wraps
from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from accounts.models import User


def backup_admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if not (request.user.is_superuser or request.user.role == User.Role.ADMIN):
            return HttpResponseForbidden("Only system administrators may manage backups.")
        return view_func(request, *args, **kwargs)
    return wrapped

