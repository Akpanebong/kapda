from django.db import migrations


def rename_promotion_values(apps, schema_editor):
    Enrolment = apps.get_model("learners", "Enrolment")
    ClassMovement = apps.get_model("learners", "ClassMovement")
    Enrolment.objects.filter(outcome="promoted").update(outcome="retained")
    ClassMovement.objects.filter(movement_type="promotion").update(movement_type="retention")


class Migration(migrations.Migration):
    dependencies = [
        ("learners", "0010_alter_classmovement_movement_type_and_more"),
    ]

    operations = [
        migrations.RunPython(rename_promotion_values, migrations.RunPython.noop),
    ]
