# Generated by Django 2.2 on 2020-09-05 13:58

import apps.users.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20200813_1305'),
    ]

    operations = [
        migrations.AddField(
            model_name='deleteduser',
            name='social_links',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=apps.users.models.default_social_links),
        ),
        migrations.AddField(
            model_name='deleteduser',
            name='tagline',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='user',
            name='social_links',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=apps.users.models.default_social_links, validators=[apps.users.models.validate_social_links]),
        ),
        migrations.AddField(
            model_name='user',
            name='tagline',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
