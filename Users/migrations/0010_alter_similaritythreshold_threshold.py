# Generated by Django 4.1.5 on 2023-01-31 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Users", "0009_similaritythreshold"),
    ]

    operations = [
        migrations.AlterField(
            model_name="similaritythreshold",
            name="threshold",
            field=models.FloatField(default=0),
        ),
    ]