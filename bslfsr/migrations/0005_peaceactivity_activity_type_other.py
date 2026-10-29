from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("bslfsr", "0004_remove_savingstransaction_group_and_more")]

    operations = [
        migrations.AddField(
            model_name="peaceactivity",
            name="activity_type_other",
            field=models.CharField(blank=True, help_text="Specify the activity type when Other is selected", max_length=160),
        ),
    ]
