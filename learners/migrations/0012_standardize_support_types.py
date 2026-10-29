from django.db import migrations, models


def standardize_support_types(apps, schema_editor):
    LearnerSupport = apps.get_model("learners", "LearnerSupport")
    mapping = {
        "scholastic": "scholastic_materials",
        "scholastic_materials": "scholastic_materials",
        "sanitary_pads": "sanitary_pads_mhm",
        "reusable_pads": "sanitary_pads_mhm",
        "mentorship": "mentorship",
        "transport": "other",
        "back_to_school": "back_to_school",
        "other": "other",
    }
    for old_value, new_value in mapping.items():
        LearnerSupport.objects.filter(support_type=old_value).update(support_type=new_value)


class Migration(migrations.Migration):
    dependencies = [("learners", "0011_rename_promotion_values")]

    operations = [
        migrations.RunPython(standardize_support_types, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="learnersupport",
            name="support_type",
            field=models.CharField(max_length=80, choices=[("scholastic_materials", "Scholastic materials"), ("sanitary_pads_mhm", "Sanitary pads / MHM support"), ("mentorship", "Mentorship"), ("back_to_school", "Back-to-school"), ("other", "Other support")]),
        ),
    ]
