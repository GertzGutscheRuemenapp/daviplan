# Generated by Django 3.2.8 on 2021-12-14 11:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datentool_backend', '0033_auto_20211209_1053'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='popstatentry',
            name='age',
        ),
    ]
