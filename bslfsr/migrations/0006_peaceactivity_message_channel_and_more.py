import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("bslfsr", "0005_peaceactivity_activity_type_other")]

    operations = [
        migrations.AddField(
            model_name="peaceactivity",
            name="message_channel",
            field=models.CharField(blank=True, choices=[("radio", "Radio"), ("community_meeting", "Community meeting"), ("school", "School"), ("religious", "Religious institution"), ("social_media", "Social media"), ("other", "Other")], max_length=80),
        ),
        migrations.AddField(
            model_name="peaceactivity",
            name="message_channel_other",
            field=models.CharField(blank=True, help_text="Specify the channel when Other is selected", max_length=160),
        ),
        migrations.CreateModel(
            name="PeaceCommitteeMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("full_name", models.CharField(max_length=180)),
                ("sex", models.CharField(choices=[("F", "Female"), ("M", "Male"), ("O", "Other / not stated")], max_length=1)),
                ("age_group", models.CharField(blank=True, max_length=60)),
                ("position", models.CharField(blank=True, max_length=120)),
                ("parish", models.CharField(blank=True, max_length=120)),
                ("sub_county", models.CharField(blank=True, max_length=120)),
                ("supported_date", models.DateField(blank=True, null=True)),
                ("active", models.BooleanField(default=True)),
                ("committee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="members", to="bslfsr.peacecommittee")),
            ],
        ),
        migrations.CreateModel(
            name="PeaceCommitteeMeeting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("parish", models.CharField(max_length=120)),
                ("sub_county", models.CharField(max_length=120)),
                ("meeting_date", models.DateField()),
                ("female_participants", models.PositiveIntegerField(default=0)),
                ("male_participants", models.PositiveIntegerField(default=0)),
                ("youth_participants", models.PositiveIntegerField(default=0)),
                ("notes", models.TextField(blank=True)),
                ("committee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="meetings", to="bslfsr.peacecommittee")),
            ],
        ),
    ]
