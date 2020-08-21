# Generated by Django 2.2 on 2020-08-21 16:59

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0002_auto_20200713_0848'),
    ]

    operations = [
        migrations.CreateModel(
            name='StackOverflowProfile',
            fields=[
                ('id', models.IntegerField(editable=False, primary_key=True, serialize=False)),
                ('reputation', models.IntegerField()),
                ('badge_counts', django.contrib.postgres.fields.jsonb.JSONField()),
                ('link', models.CharField(max_length=255)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stack_overflow', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
