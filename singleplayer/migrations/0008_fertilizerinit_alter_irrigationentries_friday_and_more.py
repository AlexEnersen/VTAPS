# Generated by Django 4.2.11 on 2024-06-24 16:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('singleplayer', '0007_fertilizerentries_irrigationentries_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FertilizerInit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week1', models.IntegerField(default=0, verbose_name='Pre-plant (week 1)')),
            ],
        ),
        migrations.AlterField(
            model_name='irrigationentries',
            name='friday',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='irrigationentries',
            name='monday',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator('0.0')]),
        ),
        migrations.AlterField(
            model_name='irrigationentries',
            name='saturday',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='irrigationentries',
            name='sunday',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='irrigationentries',
            name='thursday',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='irrigationentries',
            name='tuesday',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='irrigationentries',
            name='wednesday',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='singleplayerprofile',
            name='hybrid',
            field=models.CharField(choices=[('MZCER048', 'MZCER048')], default='BRPI0202', max_length=8),
        ),
    ]
