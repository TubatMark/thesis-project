# Generated by Django 4.1.5 on 2023-01-28 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Users", "0005_alter_admin_profile_picture_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="repositoryfiles",
            name="text_file",
            field=models.FileField(upload_to="ExtractedFiles/"),
        ),
    ]
