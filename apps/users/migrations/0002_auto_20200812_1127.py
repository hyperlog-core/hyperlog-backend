# Generated by Django 2.2 on 2020-08-12 11:27

import apps.users.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='deleteduser',
            name='login_types',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=apps.users.models.password_login_type),
        ),
        migrations.AddField(
            model_name='deleteduser',
            name='new_user',
            field=models.BooleanField(default=False, verbose_name='New User'),
        ),
        migrations.AddField(
            model_name='user',
            name='login_types',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=apps.users.models.password_login_type),
        ),
        migrations.AddField(
            model_name='user',
            name='new_user',
            field=models.BooleanField(default=False, verbose_name='New User'),
        ),
    ]