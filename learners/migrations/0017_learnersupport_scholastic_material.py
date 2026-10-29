from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("learners", "0016_alter_learneremployment_employment_type")]

    operations = [
        migrations.AddField(
            model_name="learnersupport",
            name="scholastic_material",
            field=models.CharField(
                blank=True,
                choices=[
                    ("pens", "Pens"), ("pencils", "Pencils"), ("books", "Books"),
                    ("rulers", "Rulers"), ("erasers", "Erasers"),
                    ("mathematical_set", "Mathematical set"), ("school_bag", "School bag"),
                    ("soap", "Soap"), ("sanitary_pads", "Sanitary pads"), ("other", "Other material"),
                ],
                max_length=40,
                verbose_name="Scholastic material",
            ),
        ),
    ]
