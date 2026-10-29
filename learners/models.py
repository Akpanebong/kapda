from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel, School, AcademicYear, Term, Location
from projects.models import Project


class Learner(TimeStampedModel):
    class Sex(models.TextChoices): FEMALE = "F", "Female"; MALE = "M", "Male"; OTHER = "O", "Other / not stated"
    class ParticipantCategory(models.TextChoices):
        GIRL = "girl", "Girl"
        BOY = "boy", "Boy"
        WOMAN = "woman", "Woman"
        MAN = "man", "Man"
        OTHER = "other", "Other / not stated"
    class DisplacementStatus(models.TextChoices):
        HOST = "host", "Host community"
        REFUGEE = "refugee", "Refugee"
        IDP = "idp", "Internally displaced person"
        RETURNEE = "returnee", "Returnee"
        ASYLUM_SEEKER = "asylum_seeker", "Asylum seeker"
        OTHER = "other", "Other / not stated"
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DROPOUT = "dropout", "Dropout"
        COMPLETED = "completed", "Completed"
        TRANSFERRED = "transferred", "Transferred"
        DECEASED = "deceased", "Deceased"
        ON_HOLD = "on_hold", "Temporarily not attending"
        VOCATIONAL = "vocational", "Transitioned to vocational pathway"
        UNIVERSITY = "university", "Completed – transitioned to university"
        COLLEGE = "college", "Completed – transitioned to college"
    reg_no = models.CharField(max_length=40, unique=True, editable=False, db_index=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    sex = models.CharField(max_length=1, choices=Sex.choices)
    participant_category = models.CharField(max_length=20, choices=ParticipantCategory.choices, default=ParticipantCategory.OTHER, db_index=True)
    displacement_status = models.CharField(max_length=20, choices=DisplacementStatus.choices, default=DisplacementStatus.OTHER, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    estimated_age = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(3),MaxValueValidator(30)])
    disability_status = models.BooleanField(default=False)
    disability_type = models.CharField(max_length=120, blank=True)
    admission_date = models.DateField()
    class_of_admission = models.CharField(max_length=3, choices=[(f"P{i}",f"P{i}") for i in range(1,8)]+[(f"S{i}",f"S{i}") for i in range(1,7)])
    current_class = models.CharField(max_length=3, choices=[(f"P{i}",f"P{i}") for i in range(1,8)]+[(f"S{i}",f"S{i}") for i in range(1,7)], blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    guardian_name = models.CharField(max_length=180, blank=True)
    guardian_phone = models.CharField(max_length=30, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    on_scholarship = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["last_name","first_name"]

    def save(self, *args, **kwargs):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            self.estimated_age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        if not self.current_class:
            self.current_class = self.class_of_admission
        if not self.reg_no:
            self.reg_no = "KAPDA-LEARNER-PENDING"
            super().save(*args, **kwargs)
            self.reg_no = f"KAPDA-LEARNER-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(reg_no=self.reg_no)
            if self.status == self.Status.COMPLETED:
                Enrolment.objects.filter(learner_id=self.pk).update(outcome="completed")
            return
        super().save(*args, **kwargs)
        if self.status == self.Status.COMPLETED:
            Enrolment.objects.filter(learner_id=self.pk).update(outcome="completed")

    @property
    def full_name(self): return " ".join(x for x in [self.first_name,self.middle_name,self.last_name] if x)

    @property
    def age(self):
        from datetime import date
        if self.date_of_birth:
            today=date.today()
            return today.year-self.date_of_birth.year-((today.month,today.day)<(self.date_of_birth.month,self.date_of_birth.day))
        return self.estimated_age

    @property
    def age_group(self):
        a=self.age
        if a is None: return "Unknown"
        if a <= 5: return "5 and under"
        if a <= 9: return "6–9"
        if a <= 12: return "10–12"
        if a <= 17: return "13–17"
        return "18+"

    def __str__(self):
        return f"{self.reg_no} — {self.full_name}"


class LearnerEmployment(TimeStampedModel):
    """Post-completion employment outcome for a learner."""
    class EMPLOYMENT_TYPE(models.TextChoices):
        FULL = "F", 'Full Time'
        PART = "P", 'Part Time'
        CONTRACT = "C", 'Contract'
    learner = models.OneToOneField("Learner", on_delete=models.PROTECT, related_name="employment")
    employer = models.CharField(max_length=180)
    job_title = models.CharField(max_length=180)
    year_employed = models.PositiveSmallIntegerField()
    employment_type = models.CharField(max_length=40, choices=EMPLOYMENT_TYPE.choices,
                                       blank=True, default=EMPLOYMENT_TYPE.FULL, help_text="e.g. Full-time, part-time, contract")
    work_location = models.CharField(max_length=180, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-year_employed", "employer"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.learner_id and self.learner.status != Learner.Status.COMPLETED:
            raise ValidationError("Employment outcomes can only be recorded for completed learners.")

    def __str__(self):
        return f"{self.learner.full_name} - {self.job_title} at {self.employer}"


class LearnerProject(TimeStampedModel):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="project_links")
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="learner_links")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    support_notes = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["learner","project"],
                                               name="unique_learner_project")]
    def __str__(self):
        return f"{self.learner.reg_no} / {self.project.code}"


class Enrolment(TimeStampedModel):
    learner = models.ForeignKey(Learner, on_delete=models.PROTECT, related_name="enrolments")
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="enrolments")
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="enrolments")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    class_level = models.CharField(max_length=3, choices=[(f"P{i}",f"P{i}") for i in range(1,8)]+[(f"S{i}",f"S{i}") for i in range(1,7)])
    is_current = models.BooleanField(default=True, db_index=True)
    outcome = models.CharField("Status", max_length=20, choices=[("enrolled","Enrolled"),("retained","Retained"),("repeated","Repeated"),("completed","Completed"),("transferred","Transferred"),("dropout","Dropout")], default="enrolled")

    class Meta:
        ordering = ["-academic_year__start_date","class_level"]
        constraints = [
            models.UniqueConstraint(fields=["learner", "school"], name="one_enrolment_per_learner_school"),
            models.UniqueConstraint(fields=["learner"], condition=models.Q(is_current=True), name="one_current_enrolment_per_learner"),
        ]

    def save(self, *args, **kwargs):
        if self.is_current and self.learner_id:
            current = type(self).objects.filter(learner_id=self.learner_id, is_current=True).exclude(pk=self.pk)
            for old in current.only("pk", "school_id"):
                type(self).objects.filter(pk=old.pk).update(
                    is_current=False,
                    outcome="transferred" if old.school_id != self.school_id else "retained",
                    updated_at=timezone.now(),
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.learner.reg_no} — {self.class_level} ({self.academic_year})"


class ClassMovement(TimeStampedModel):
    learner = models.ForeignKey(Learner, on_delete=models.PROTECT, related_name="class_movements")
    from_enrolment = models.ForeignKey(Enrolment, on_delete=models.PROTECT, related_name="movements_from")
    to_enrolment = models.ForeignKey(Enrolment, null=True, blank=True, on_delete=models.PROTECT, related_name="movements_to")
    movement_type = models.CharField(max_length=20, choices=[("retention","Retention"),("repeat","Repeat"),("transition","School-cycle transition"),("transfer","School transfer"),("completion","Completion"),("dropout","Dropout")])
    effective_date = models.DateField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)


class AttendanceRecord(TimeStampedModel):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="attendance_records")
    enrolment = models.ForeignKey(Enrolment, on_delete=models.CASCADE, related_name="attendance")
    term = models.ForeignKey(Term, on_delete=models.PROTECT)
    days_open = models.PositiveSmallIntegerField(default=0)
    days_present = models.PositiveSmallIntegerField(default=0)
    days_absent = models.PositiveSmallIntegerField(default=0)
    consecutive_absence_days = models.PositiveSmallIntegerField(default=0)
    absence_reason = models.CharField(max_length=160, blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["learner","enrolment","term"],
                                               name="unique_learner_term_attendance")]

    @property
    def attendance_rate(self):
        return round((self.days_present / self.days_open) * 100, 1) if self.days_open else 0


class Assessment(TimeStampedModel):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name="assessments")
    enrolment = models.ForeignKey(Enrolment, on_delete=models.CASCADE, related_name="assessments")
    term = models.ForeignKey(Term, on_delete=models.PROTECT)
    subject = models.CharField(max_length=100)
    score = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    maximum_score = models.DecimalField(max_digits=6, decimal_places=2, default=100, validators=[MinValueValidator(1)])
    grade = models.CharField(max_length=10, blank=True)
    comments = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ["learner","subject","term"]
    @property
    def percentage(self):
        return round(float(self.score / self.maximum_score * 100), 2) if self.maximum_score else 0


class UNEBResult(TimeStampedModel):
    learner = models.ForeignKey(Learner, on_delete=models.PROTECT, related_name="uneb_results")
    school = models.ForeignKey(School, on_delete=models.PROTECT)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT)
    examination_year = models.PositiveSmallIntegerField()
    candidate_number = models.CharField(max_length=60, blank=True)
    level = models.CharField(max_length=10, choices=[("UCE","UCE / S4"),("UACE","UACE / S6")], default="UCE")
    aggregate_or_points = models.CharField(max_length=30, blank=True)
    division_grade = models.CharField(max_length=30, blank=True)
    subjects = models.JSONField(default=dict, blank=True, help_text="Subject grades as a JSON object")
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["learner","examination_year","level"],
                                               name="unique_learner_uneb_level_year")]


class LearnerStatusHistory(TimeStampedModel):
    learner = models.ForeignKey(Learner, on_delete=models.PROTECT, related_name="status_history")
    previous_status = models.CharField(max_length=20, choices=Learner.Status.choices, blank=True)
    new_status = models.CharField(max_length=20, choices=Learner.Status.choices)
    effective_date = models.DateField()
    reason = models.CharField(max_length=180, blank=True)
    follow_up_action = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-effective_date","-created_at"]

    def save(self, *args, **kwargs):
        from django.db import transaction
        if self.learner_id:
            learner = Learner.objects.get(pk=self.learner_id)
            if not self.previous_status:
                self.previous_status = learner.status
        with transaction.atomic():
            super().save(*args, **kwargs)
            Learner.objects.filter(pk=self.learner_id).update(
                status=self.new_status,
                updated_at=timezone.now(),
            )
            outcome_by_status = {
                Learner.Status.ACTIVE: "enrolled",
                Learner.Status.COMPLETED: "completed",
                Learner.Status.DROPOUT: "dropout",
                Learner.Status.TRANSFERRED: "transferred",
                Learner.Status.VOCATIONAL: "completed",
                Learner.Status.UNIVERSITY: "completed",
                Learner.Status.COLLEGE: "completed",
            }
            outcome = outcome_by_status.get(self.new_status)
            if outcome:
                updates = {"outcome": outcome}
                if self.new_status == Learner.Status.TRANSFERRED:
                    updates["is_current"] = False
                Enrolment.objects.filter(learner_id=self.learner_id, is_current=True).update(**updates)


class LearnerSupport(TimeStampedModel):
    learner = models.ForeignKey(Learner, on_delete=models.PROTECT, related_name="supports")
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    support_type = models.CharField(max_length=80, choices=[("scholastic_materials", "Scholastic materials"), ("sanitary_pads_mhm", "Sanitary pads / MHM support"), ("mentorship", "Mentorship"), ("back_to_school", "Back-to-school"), ("other", "Other support")])
    support_type_other = models.CharField(max_length=160, blank=True, verbose_name="Specify other support")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=40, default="package")
    distribution_date = models.DateField()
    term = models.ForeignKey(Term, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
