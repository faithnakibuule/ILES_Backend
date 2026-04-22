from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("logbook", "0006_alter_weeklylog_submitted_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="weeklylog",
            name="activities",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="weeklylog",
            name="learning_points",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="weeklylog",
            name="status",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"),
                    ("MISSED", "Missed"),
                    ("SUBMITTED", "Submitted"),
                    ("REVIEWED", "Reviewed"),
                    ("APPROVED", "Approved"),
                ],
                default="DRAFT",
                max_length=20,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="weeklylog",
            unique_together={("intern", "placement", "week_number")},
        ),
    ]
