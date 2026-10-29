import secrets
import string

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import User


def generate_staff_id(exclude_pk=None):
    """Return the next unique KAPDA-YY-NN staff identifier."""
    from django.utils import timezone

    prefix = f"KAPDA-{timezone.localdate().year % 100:02d}-"
    number = 1
    while User.objects.filter(reg_no=f"{prefix}{number:02d}").exclude(pk=exclude_pk).exists() or User.objects.filter(username__iexact=f"{prefix}{number:02d}").exclude(pk=exclude_pk).exists():
        number += 1
    return f"{prefix}{number:02d}"


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username, email, phone or RegNo", widget=forms.TextInput(attrs={"autofocus":True,"placeholder":"Enter username, email, phone or RegNo"}))

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError("This application is restricted to authorized KAPDA staff.", code="staff_only")


class StaffForm(forms.ModelForm):
    password = forms.CharField(required=False, widget=forms.TextInput(attrs={"autocomplete": "off"}))

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "reg_no", "role",
                  "job_title", "department", "photo", "is_active",
                  ] #"must_change_password", "is_staff", "projects",

    def __init__(self, *args, creating=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.creating = self.instance.pk is None if creating is None else creating
        self.generated_staff_id = generate_staff_id(self.instance.pk)
        self.fields["username"].widget.attrs.update({"readonly": "readonly", "autocomplete": "off"})
        self.fields["reg_no"].widget.attrs.update({"readonly": "readonly", "autocomplete": "off"})
        self.fields["username"].help_text = "Automatically generated from the KAPDA staff ID."
        self.fields["reg_no"].help_text = "Automatically generated staff ID; it is also the username."
        if self.creating:
            self.fields["username"].initial = self.generated_staff_id
            self.fields["reg_no"].initial = self.generated_staff_id
            self.fields["password"].initial = self._generated_password()
            self.fields["password"].widget.attrs.update({"readonly": "readonly"})
            self.fields["password"].help_text = "Automatically generated. The staff member can change it using Forgot password."
        else:
            self.fields.pop("password")

    @staticmethod
    def _generated_password():
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        return "Kpda-" + "".join(secrets.choice(alphabet) for _ in range(12))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if self.creating:
            user.username = self.generated_staff_id
            user.reg_no = self.generated_staff_id
        password = self.cleaned_data.get("password") if self.creating else None
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user


class CredentialResetForm(forms.Form):
    username = forms.CharField(label="Username", max_length=150)
    current_password = forms.CharField(label="Current password", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm new password", widget=forms.PasswordInput)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["username"].initial = user.username

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise ValidationError("That username is already in use. Please choose another one.")
        return username

    def clean_current_password(self):
        current_password = self.cleaned_data["current_password"]
        if not self.user.check_password(current_password):
            raise ValidationError("Your current password is incorrect.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            self.add_error("new_password2", "The new passwords do not match.")
        if password1:
            validate_password(password1, self.user)
        return cleaned_data
