# Generated by Django 2.2 on 2020-11-05 15:28

import apps.base.utils
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramUser',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=64)),
                ('last_name', models.CharField(blank=True, max_length=64, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MessageFromTelegram',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_message_id', models.IntegerField()),
                ('text', models.TextField()),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('receiver', models.ForeignKey(on_delete=models.SET(apps.base.utils.get_sentinel_user), related_name='received_messages_from_tg', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=models.SET(apps.base.utils.get_sentinel_user), related_name='sent_messages', to='messaging.TelegramUser')),
            ],
        ),
    ]