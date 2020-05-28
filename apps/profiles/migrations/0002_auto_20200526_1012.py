# Generated by Django 2.2 on 2020-05-26 10:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("profiles", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="baseprofilemodel",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="profiles",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="BitbucketProfile",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": [],},
            bases=("profiles.baseprofilemodel",),
        ),
        migrations.CreateModel(
            name="GithubProfile",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": [],},
            bases=("profiles.baseprofilemodel",),
        ),
        migrations.CreateModel(
            name="GitlabProfile",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": [],},
            bases=("profiles.baseprofilemodel",),
        ),
        migrations.AlterUniqueTogether(
            name="baseprofilemodel",
            unique_together={("_provider", "username")},
        ),
    ]