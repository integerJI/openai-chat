# Generated by Django 5.0.7 on 2024-09-14 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='user_id',
            field=models.CharField(default='', max_length=100),
        ),
    ]
