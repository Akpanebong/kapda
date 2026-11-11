from django.db import migrations
from django.utils.text import slugify
from uuid import uuid4


SLUGGED_MODELS = (
    ("core", "location"), ("core", "school"), ("core", "household"),
    ("core", "academicyear"), ("core", "term"), ("core", "fieldattendance"),
    ("core", "fieldattendanceparticipant"), ("accounts", "user"),
    ("projects", "project"), ("projects", "indicator"),
    ("projects", "monitoringform"), ("projects", "activitydata"),
    ("learners", "learner"), ("learners", "learneremployment"),
    ("learners", "learnerproject"), ("learners", "enrolment"),
    ("learners", "classmovement"), ("learners", "attendancerecord"),
    ("learners", "assessment"), ("learners", "unebresult"),
    ("learners", "learnerstatushistory"), ("learners", "learnersupport"),
    ("monitoring", "fieldvisit"), ("monitoring", "followupaction"),
    ("monitoring", "mhmsession"), ("monitoring", "washfacility"),
    ("school_governance", "governancemember"), ("school_governance", "governancemeeting"),
    ("school_governance", "governancetraining"), ("school_governance", "schoolimprovementplan"),
    ("school_governance", "governanceaction"), ("bslfsr", "beneficiary"),
    ("bslfsr", "farmerrecord"), ("bslfsr", "peaceactivity"),
    ("bslfsr", "peacecommittee"), ("bslfsr", "peacecommitteemember"),
    ("bslfsr", "peacecommitteemeeting"), ("vsla", "vslamember"),
    ("vsla", "loan"), ("vsla", "vsla_meeting"), ("backups", "backupjob"),
)


def backfill_slugs(apps, schema_editor):
    for app_label, model_name in SLUGGED_MODELS:
        model = apps.get_model(app_label, model_name)
        fields = {field.name for field in model._meta.fields}
        for record in model.objects.filter(slug__isnull=True).iterator():
            source = None
            for field_name in ("full_name", "name", "title", "code", "reg_no", "beneficiary_id", "committee_id", "household_id", "loan_no", "member_no", "transaction_ref"):
                if field_name in fields and getattr(record, field_name, None):
                    source = str(getattr(record, field_name))
                    break
            source = source or model_name
            record.slug = f"{slugify(source)[:210]}-{uuid4().hex[:10]}"
            record.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_academicyear_slug_fieldattendance_slug_and_more"),
        ("accounts", "0005_user_slug"),
        ("backups", "0002_backupjob_slug"),
        ("bslfsr", "0009_beneficiary_slug_farmerrecord_slug_and_more"),
        ("learners", "0020_assessment_slug_attendancerecord_slug_and_more"),
        ("monitoring", "0003_fieldvisit_slug_followupaction_slug_mhmsession_slug_and_more"),
        ("projects", "0022_activitydata_slug_indicator_slug_monitoringform_slug_and_more"),
        ("school_governance", "0003_governanceaction_slug_governancemeeting_slug_and_more"),
        ("vsla", "0005_loan_slug_vslamember_slug"),
    ]

    operations = [migrations.RunPython(backfill_slugs, migrations.RunPython.noop)]
