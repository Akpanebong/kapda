import logging
import uuid

from django.core.cache import cache
from django.http import HttpResponseNotAllowed
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect

from core.error_reporting import send_error_report

logger = logging.getLogger(__name__)


def _fallback_report(request):
    user = getattr(request, "user", None)
    authenticated = bool(user and getattr(user, "is_authenticated", False))
    return {
        "report_id": uuid.uuid4().hex,
        "exception_type": "Unhandled server error",
        "exception_message": "The application could not complete this request.",
        "traceback": "No traceback was available from the server.",
        "request": {
            "method": request.method,
            "path": request.get_full_path(),
            "absolute_uri": request.get_full_path(),
            "user": str(user) if authenticated else "AnonymousUser",
            "user_id": getattr(user, "pk", None) if authenticated else None,
            "meta": {
                "REMOTE_ADDR": request.META.get("REMOTE_ADDR", "Unknown"),
                "HTTP_USER_AGENT": request.META.get("HTTP_USER_AGENT", "Unknown")[:1000],
                "HTTP_REFERER": request.META.get("HTTP_REFERER", "Not provided")[:1000],
            },
        },
    }


def custom_500_view(request):
    report = getattr(request, "_error_report_context", None) or _fallback_report(request)
    report_id = report.get("report_id") or uuid.uuid4().hex
    report["report_id"] = report_id
    cache.set(f"error-report:{report_id}", report, timeout=3600)
    return render(request, "errors/500.html", {"report_id": report_id, "error_message": report.get("exception_message")}, status=500)


def custom_404_view(request, exception):
    return render(request, "errors/404.html", {"requested_path": request.get_full_path()}, status=404)


def custom_403_view(request, exception):
    return render(request, "errors/403.html", status=403)


def custom_400_view(request, exception):
    return render(request, "errors/400.html", status=400)


@csrf_protect
def report_500_error(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    report_id = request.POST.get("report_id", "").strip()
    report = cache.get(f"error-report:{report_id}") if report_id else None
    if not report:
        return render(request, "errors/report_result.html", {"sent": False, "error": "This error report has expired. Please reproduce the error and try again."}, status=410)
    try:
        send_error_report(report)
    except Exception:
        logger.exception("Could not send error report %s", report_id)
        return render(request, "errors/report_result.html", {"sent": False, "error": "The report could not be sent right now. Please contact the system administrator."}, status=503)
    cache.delete(f"error-report:{report_id}")
    return render(request, "errors/report_result.html", {"sent": True})

