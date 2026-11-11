from django.db import migrations
from django.utils.text import slugify
from uuid import uuid4


MODEL_LABELS = (
    ("core", "location"), ("core", "school"), ("core", "household"),
    ("core", "academicyear"), ("core", "term"), ("core", "fieldattendance"),
    ("core", "fieldattendanceparticipant"), ("accounts", "user"),
    ("projects", "project"), ("projects", "indicator"), ("projects", "monitoringform"),
    ("projects", "activitydata"), ("learners", "learner"), ("learners", "learneremployment"),
    ("learners", "learnerproject"), ("learners", "enrolment"), ("learners", "classmovement"),
    ("learners", "attendancerecord"), ("learners", "assessment"), ("learners", "unebresult"),
    ("learners", "learnerstatushistory"), ("learners", "learnersupport"),
    ("monitoring", "fieldvisit"), ("monitoring", "followupaction"), ("monitoring", "mhmsession"),
    ("monitoring", "washfacility"), ("school_governance", "governancemember"),
    ("school_governance", "governancemeeting"), ("school_governance", "governancetraining"),
    ("school_governance", "schoolimprovementplan"), ("school_governance", "governanceaction"),
    ("bslfsr", "beneficiary"), ("bslfsr", "farmerrecord"), ("bslfsr", "peaceactivity"),
    ("bslfsr", "peacecommittee"), ("bslfsr", "peacecommitteemember"),
    ("bslfsr", "peacecommitteemeeting"), ("vsla", "vslagroup"), ("vsla", "vslamember"), ("vsla", "loan"),
    ("vsla", "vsla_meeting"), ("backups", "backupjob"),
)


def rotate_slugs(apps, schema_editor):
    for app_label, model_name in MODEL_LABELS:
        model = apps.get_model(app_label, model_name)
        fields = {field.name for field in model._meta.fields}
        for record in model.objects.all().iterator():
            source = next((str(getattr(record, field)) for field in ("full_name", "name", "title", "code", "reg_no", "beneficiary_id", "committee_id", "household_id", "loan_no", "member_no", "transaction_ref") if field in fields and getattr(record, field, None)), model_name)
            record.slug = f"{slugify(source)[:210]}-{uuid4().hex[:10]}"
            record.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [("core", "0009_backfill_missing_slugs")]
    operations = [migrations.RunPython(rotate_slugs, migrations.RunPython.noop)]
