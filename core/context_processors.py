from django.utils import timezone
def kapda_context(request):
    return {
        "organization_name": "KAPDA",
        "organization_tagline": "Belong to one another",
        "system_name": "KAPDA Programme & Learning Information System",
        "today": timezone.localdate(),
    }
