# Generated by Django 5.0.1 on 2024-10-18 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('singleplayer', '0012_alter_singleplayerprofile_seeding_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='singleplayerprofile',
            name='fert_id',
            field=models.IntegerField(default=-1),
        ),
    ]
