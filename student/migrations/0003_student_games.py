# Generated by Django 5.1.2 on 2025-07-15 02:51

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0002_student_activation_key_student_confirmed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='games',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256), blank=True, default=list, size=None),
        ),
    ]
