# Generated by Django 5.2 on 2025-05-04 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jssp', '0003_partno_partcolor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partno',
            name='partno_ascii',
            field=models.CharField(blank=True, max_length=2, null=True),
        ),
    ]
