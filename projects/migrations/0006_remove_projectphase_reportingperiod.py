from django.db import migrations, models


def copy_reporting_period_kind(apps, schema_editor):
    ActivityData = apps.get_model("projects", "ActivityData")
    ReportingPeriod = apps.get_model("projects", "ReportingPeriod")
    kinds = dict(ReportingPeriod.objects.values_list("pk", "kind"))
    for entry in ActivityData.objects.all().only("pk", "reporting_period"):
        kind = kinds.get(entry.reporting_period_id)
        if kind:
            ActivityData.objects.filter(pk=entry.pk).update(legacy_reporting_period=kind)


class Migration(migrations.Migration):
    dependencies = [("projects", "0005_alter_activitydata_age_and_more")]

    operations = [
        migrations.AddField(
            model_name="activitydata",
            name="legacy_reporting_period",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.RunPython(copy_reporting_period_kind, migrations.RunPython.noop),
        migrations.RemoveField(model_name="activitydata", name="reporting_period"),
        migrations.RenameField(
            model_name="activitydata",
            old_name="legacy_reporting_period",
            new_name="reporting_period",
        ),
        migrations.AlterField(
            model_name="activitydata",
            name="reporting_period",
            field=models.CharField(blank=True, choices=[("month", "Month"), ("quarter", "Quarter"), ("term", "Term"), ("season", "Season"), ("annual", "Annual")], max_length=20),
        ),
        migrations.DeleteModel(name="ReportingPeriod"),
        migrations.DeleteModel(name="ProjectPhase"),
    ]
