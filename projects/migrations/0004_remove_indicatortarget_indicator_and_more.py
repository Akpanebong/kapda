from collections import defaultdict

from django.db import migrations, models


def move_period_targets_to_indicator(apps, schema_editor):
    Indicator = apps.get_model("projects", "Indicator")
    IndicatorTarget = apps.get_model("projects", "IndicatorTarget")
    totals = defaultdict(lambda: 0)
    for row in IndicatorTarget.objects.values("indicator_id", "target_value"):
        totals[row["indicator_id"]] += row["target_value"] or 0
    for indicator_id, total in totals.items():
        Indicator.objects.filter(pk=indicator_id).update(target=total)


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0003_remove_indicator_disaggregate_age_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="indicator",
            old_name="project_target",
            new_name="target",
        ),
        migrations.AddField(
            model_name="indicator",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="indicator",
            name="start_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="indicator",
            name="status",
            field=models.CharField(
                choices=[
                    ("planned", "Planned"),
                    ("in_progress", "In progress"),
                    ("completed", "Completed"),
                    ("overdue", "Overdue"),
                    ("cancelled", "Cancelled"),
                ],
                db_index=True,
                default="planned",
                max_length=20,
            ),
        ),
        migrations.RunPython(move_period_targets_to_indicator, migrations.RunPython.noop),
        migrations.DeleteModel(name="IndicatorActual"),
        migrations.DeleteModel(name="IndicatorTarget"),
    ]
