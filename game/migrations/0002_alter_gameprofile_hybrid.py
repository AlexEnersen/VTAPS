# Generated by Django 5.1.2 on 2025-07-24 19:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gameprofile',
            name='hybrid',
            field=models.CharField(choices=[('MZCER048', 'MZCER048')], default=None, max_length=8),
        ),
    ]
