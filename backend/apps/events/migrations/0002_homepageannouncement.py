from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomepageAnnouncement",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("enabled", models.BooleanField(default=False)),
                ("eyebrow", models.CharField(default="Latest update", max_length=100)),
                ("title", models.CharField(blank=True, max_length=255)),
                ("message", models.TextField(blank=True)),
                ("image_url", models.URLField(blank=True, max_length=1000)),
                ("action_label", models.CharField(blank=True, max_length=100)),
                ("action_url", models.CharField(blank=True, max_length=1000)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
