import logging
import traceback
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)
ERROR_REPORT_TIMEOUT = 60 * 60


def _request_details(request):
    meta = {
        key: value
        for key, value in request.META.items()
        if (key.startswith("HTTP_") or key in {"REMOTE_ADDR", "SERVER_NAME", "SERVER_PORT", "SERVER_PROTOCOL"})
        and key not in {"HTTP_COOKIE", "HTTP_AUTHORIZATION"}
        and "PASSWORD" not in key
    }
    try:
        absolute_uri = request.build_absolute_uri()
    except Exception:
        absolute_uri = request.get_full_path()
    user = getattr(request, "user", None)
    authenticated = bool(user and getattr(user, "is_authenticated", False))
    return {
        "method": request.method,
        "path": request.get_full_path(),
        "absolute_uri": absolute_uri,
        "user": str(user) if authenticated else "AnonymousUser",
        "user_id": getattr(user, "pk", None) if authenticated else None,
        "meta": meta,
    }


def create_error_report(request, exception):
    report_id = uuid.uuid4().hex
    details = {
        "report_id": report_id,
        "exception_type": type(exception).__name__,
        "exception_message": str(exception) or "No exception message was provided.",
        "traceback": "".join(traceback.format_exception(type(exception), exception, exception.__traceback__)),
        "request": _request_details(request),
    }
    cache.set(f"error-report:{report_id}", details, ERROR_REPORT_TIMEOUT)
    return report_id, details


class ErrorReportingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            if response.status_code in {400, 403, 404}:
                template = {400: "errors/400.html", 403: "errors/403.html", 404: "errors/404.html"}[response.status_code]
                response = HttpResponse(render_to_string(template, {"requested_path": request.get_full_path()}, request=request), status=response.status_code)
            return response
        except SuspiciousOperation:
            logger.exception("Rejected KAPDA request")
            return HttpResponse(render_to_string("errors/400.html", request=request), status=400)
        except Exception as exception:
            report_id, details = create_error_report(request, exception)
            request._error_report_context = details
            logger.exception("Unhandled KAPDA application error %s", report_id)
            html = render_to_string("errors/500.html", {"report_id": report_id, "error_message": details["exception_message"]}, request=request)
            return HttpResponse(html, status=500)


def send_error_report(details):
    recipient = getattr(settings, "EMAIL_HOST_USER", "") or getattr(settings, "DEFAULT_FROM_EMAIL", "")
    sender = getattr(settings, "DEFAULT_FROM_EMAIL", "") or recipient
    if not recipient:
        raise ValueError("Configure EMAIL_HOST_USER or DEFAULT_FROM_EMAIL before reporting errors.")
    subject = f"KAPDA application error [{details['report_id']}]"
    body = render_to_string("errors/error_report.txt", {"details": details})
    EmailMessage(subject, body, sender, [recipient]).send(fail_silently=False)
