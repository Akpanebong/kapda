from django.conf import settings
from django.db import models
from django.utils import timezone
from uuid import uuid4


def initials_from_name(value):
    words = [word for word in (value or "").strip().split() if word]
    if not words:
        return ""
    return "".join(word[0] for word in words[:3]).upper()

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class Location(TimeStampedModel):
    district = models.CharField(max_length=120, db_index=True)
    county = models.CharField(max_length=120, blank=True)
    sub_county = models.CharField(max_length=120, blank=True, db_index=True)
    parish = models.CharField(max_length=120, blank=True, db_index=True)
    village = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return " / ".join(x for x in [self.village, self.parish, self.sub_county, self.district] if x)


class School(TimeStampedModel):
    name = models.CharField(max_length=200, db_index=True)
    school_code = models.CharField(max_length=40, unique=True, blank=True, editable=False)
    school_type = models.CharField(max_length=20, choices=[("primary","Primary"),("secondary","Secondary"),("mixed","Mixed"),("vocational","Vocational")], default="primary")
    ownership = models.CharField(max_length=30, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    active = models.BooleanField(default=True)
    kapda_supported = models.BooleanField(default=False)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def save(self, *args, **kwargs):
        new_record = self._state.adding
        if not self.school_code:
            self.school_code = f"KAPDA-SCHOOL-PENDING-{uuid4().hex[:8].upper()}"
            super().save(*args, **kwargs)
            self.school_code = f"KAPDA-SCHOOL-{self.pk:04d}"
            type(self).objects.filter(pk=self.pk).update(school_code=self.school_code)
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.school_code})"


class Household(TimeStampedModel):
    household_id = models.CharField(max_length=40, unique=True, editable=False)
    household_head = models.CharField(max_length=180, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.household_id:
            self.household_id = f"KAPDA-HH-PENDING-{uuid4().hex[:8].upper()}"
            super().save(*args, **kwargs)
            self.household_id = f"KAPDA-HH-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(household_id=self.household_id)
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.household_id} — {self.household_head or 'Household'}"


class AcademicYear(TimeStampedModel):
    name = models.CharField(max_length=30, unique=True, help_text="e.g. 2026/2027")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def save(self, *args, **kwargs):
        if self.is_current:
            type(self).objects.exclude(pk=self.pk).filter(is_current=True).update(
                is_current=False,
                updated_at=timezone.now(),
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Term(TimeStampedModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="terms")
    name = models.CharField(max_length=30, choices=[("Term 1","Term 1"),("Term 2","Term 2"),("Term 3","Term 3"),("Annual","Annual")])
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["academic_year","name"], name="unique_term_per_year")]
        ordering = ["academic_year","start_date"]

    def __str__(self):
        return f"{self.academic_year} — {self.name}"


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    model_label = models.CharField(max_length=120)
    object_id = models.CharField(max_length=80, blank=True)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action}: {self.model_label} {self.object_id}"


class FieldAttendance(TimeStampedModel):
    """Header information for the KAPDA field activity attendance sheet."""
    district = models.CharField(max_length=120)
    county = models.CharField(max_length=120, blank=True)
    sub_county = models.CharField(max_length=120, blank=True)
    parish = models.CharField(max_length=120, blank=True)
    village = models.CharField(max_length=120, blank=True)
    activity_date = models.DateField()
    activity = models.ForeignKey("projects.Indicator", on_delete=models.CASCADE, null=True, blank=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="submitted_attendance_sheets")
    submitted_title = models.CharField(max_length=160, blank=True)
    submitted_signature = models.CharField(max_length=240, blank=True)
    submitted_date = models.DateField(null=True, blank=True)
    approved_by = models.CharField(max_length=180, blank=True)
    approved_title = models.CharField(max_length=160, blank=True)
    approved_signature = models.CharField(max_length=240, blank=True)
    approved_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[("pending", "Pending approval"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", db_index=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_attendance_sheets")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-activity_date", "-created_at"]

    def __str__(self):
        return f"{self.activity} - {self.activity_date}"


class FieldAttendanceParticipant(TimeStampedModel):
    attendance = models.ForeignKey(FieldAttendance, on_delete=models.CASCADE, related_name="participants")
    name = models.CharField(max_length=180)
    sex = models.CharField(max_length=1, choices=[("M", "Male"), ("F", "Female"), ("O", "Other / not stated")])
    title_role = models.CharField(max_length=160, blank=True)
    contact = models.CharField(max_length=120, blank=True, help_text="Email or telephone number")
    signature = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["pk"]
