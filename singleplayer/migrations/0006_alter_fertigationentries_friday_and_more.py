# Generated by Django 4.2.7 on 2024-02-21 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('singleplayer', '0005_fertigationentries'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fertigationentries',
            name='friday',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='fertigationentries',
            name='monday',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='fertigationentries',
            name='saturday',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='fertigationentries',
            name='sunday',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='fertigationentries',
            name='thursday',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='fertigationentries',
            name='tuesday',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='fertigationentries',
            name='wednesday',
            field=models.IntegerField(default=0),
        ),
    ]
