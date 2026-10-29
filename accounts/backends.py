from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class MultiIdentifierBackend(ModelBackend):
    """Authenticate with username, email, phone number, or registered RegNo."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identifier = username or kwargs.get("identifier") or kwargs.get(User.USERNAME_FIELD)
        if not identifier or not password: return None
        try:
            user = User.objects.get(Q(username__iexact=identifier) | Q(email__iexact=identifier) |
                                    Q(phone=identifier) | Q(reg_no__iexact=identifier))
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
