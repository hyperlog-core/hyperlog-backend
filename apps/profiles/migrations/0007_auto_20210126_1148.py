# Generated by Django 2.2 on 2021-01-26 11:48

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_techanalysis'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseprofilemodel',
            name='profile_analysis',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.CreateModel(
            name='Repo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('provider_repo_id', models.IntegerField()),
                ('provider', models.CharField(max_length=20)),
                ('full_name', models.CharField(max_length=255)),
                ('repo_analysis', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'unique_together': {('provider', 'provider_repo_id')},
            },
        ),
    ]