from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reviews", "0003_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="evaluation",
            name="objectives",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="evaluation",
            name="rating",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="evaluation",
            name="recommendation",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="evaluation",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="evaluation",
            name="comments",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="evaluation",
            name="criteria_scores",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterModelOptions(
            name="evaluation",
            options={"ordering": ["-created_at"]},
        ),
    ]
