# Generated by Django 3.2.12 on 2022-04-13 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datentool_backend', '0096_year_is_real'),
    ]

    operations = [
        migrations.AddField(
            model_name='area',
            name='is_cut',
            field=models.BooleanField(default=False),
        ),
    ]