from django.db import migrations, models
import django.db.models.deletion


def copy_term_reference(apps, schema_editor):
    ActivityData = apps.get_model("projects", "ActivityData")
    Term = apps.get_model("core", "Term")
    names = {
        "term_1": "Term 1",
        "term_2": "Term 2",
        "term_3": "Term 3",
        "annual": "Annual",
    }
    terms = {}
    for term in Term.objects.all().order_by("academic_year_id", "pk"):
        terms.setdefault(term.name, term.pk)
    for entry in ActivityData.objects.all().only("pk", "term_or_period"):
        term_id = terms.get(names.get(entry.term_or_period, entry.term_or_period))
        if term_id:
            ActivityData.objects.filter(pk=entry.pk).update(legacy_term_or_period_id=term_id)


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0006_remove_projectphase_reportingperiod"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="activitydata",
            name="legacy_term_or_period",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.term"),
        ),
        migrations.RunPython(copy_term_reference, migrations.RunPython.noop),
        migrations.RemoveField(model_name="activitydata", name="term_or_period"),
        migrations.RenameField(
            model_name="activitydata",
            old_name="legacy_term_or_period",
            new_name="term_or_period",
        ),
        migrations.AlterField(
            model_name="activitydata",
            name="term_or_period",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_data", to="core.term"),
        ),
        migrations.AlterField(
            model_name="activitydata",
            name="class_level",
            field=models.CharField(blank=True, choices=[("P1", "P1"), ("P2", "P2"), ("P3", "P3"), ("P4", "P4"), ("P5", "P5"), ("P6", "P6"), ("P7", "P7"), ("S1", "S1"), ("S2", "S2"), ("S3", "S3"), ("S4", "S4"), ("S5", "S5"), ("S6", "S6")], max_length=3),
        ),
    ]
