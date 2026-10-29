from django.http import HttpResponseForbidden


class StaffOnlyMiddleware:
    """Keep the programme application available only to active NGO staff."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        public_prefixes = ("/accounts/login/", "/static/", "/media/", "/admin/")
        if request.path.startswith(public_prefixes):
            return self.get_response(request)
        if request.user.is_authenticated and not request.user.is_staff:
            return HttpResponseForbidden("This application is restricted to authorized KAPDA NGO staff.")
        return self.get_response(request)
