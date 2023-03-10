# Generated by Django 4.1.5 on 2023-03-02 03:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Users", "0002_remove_uploaddocuments_student_proponents_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentsProponents",
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
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.AlterField(
            model_name="documents",
            name="docs_title",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RemoveField(
            model_name="documents",
            name="proponents",
        ),
        migrations.AlterField(
            model_name="proponent",
            name="name",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="documents",
            name="proponents",
            field=models.ManyToManyField(
                related_name="proponents", to="Users.documentsproponents"
            ),
        ),
    ]
