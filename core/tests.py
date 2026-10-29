from django.core import mail
from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import reverse

from .error_reporting import create_error_report, send_error_report


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_HOST_USER="errors@example.org",
    DEFAULT_FROM_EMAIL="noreply@example.org",
)
class ErrorReportingTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def tearDown(self):
        cache.clear()

    def test_report_contains_traceback_and_request_context(self):
        request = self.factory.get("/broken/?from=test")
        try:
            raise RuntimeError("database unavailable")
        except RuntimeError as exception:
            report_id, details = create_error_report(request, exception)

        self.assertEqual(report_id, cache.get(f"error-report:{report_id}")["report_id"])
        self.assertIn("RuntimeError: database unavailable", details["traceback"])
        self.assertEqual(details["request"]["path"], "/broken/?from=test")

    def test_sends_complete_report_to_email_host_user(self):
        details = {
            "report_id": "abc123",
            "exception_type": "ValueError",
            "exception_message": "bad value",
            "traceback": "ValueError: bad value",
            "request": {
                "method": "GET",
                "path": "/broken/",
                "absolute_uri": "https://example.org/broken/",
                "user": "staff",
                "user_id": 7,
                "meta": {},
            },
        }

        send_error_report(details)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["errors@example.org"])
        self.assertIn("ValueError: bad value", mail.outbox[0].body)

    def test_report_button_posts_and_consumes_stored_report(self):
        details = {
            "report_id": "button123",
            "exception_type": "RuntimeError",
            "exception_message": "broken",
            "traceback": "RuntimeError: broken",
            "request": {"method": "GET", "path": "/", "absolute_uri": "http://testserver/", "user": "staff", "user_id": 1, "meta": {}},
        }
        cache.set("error-report:button123", details)

        response = self.client.post(reverse("errors:report"), {"report_id": "button123"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Error reported")
        self.assertIsNone(cache.get("error-report:button123"))
