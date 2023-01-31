# Generated by Django 4.1.5 on 2023-01-30 18:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("Users", "0008_alter_admin_profile_picture_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SimilarityThreshold",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("threshold", models.FloatField(null=True)),
                (
                    "user",
                    models.OneToOneField(
                        default=1,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "db_similarity_threshold",
            },
        ),
    ]