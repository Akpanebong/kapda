from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("learners", "0017_learnersupport_scholastic_material")]

    operations = [
        migrations.AddField(
            model_name="learnersupport",
            name="material_items",
            field=models.JSONField(blank=True, default=list, help_text="Multiple scholastic materials with quantities and units"),
        ),
    ]
