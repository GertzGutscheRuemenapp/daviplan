# Generated by Django 3.2.12 on 2022-04-01 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datentool_backend', '0091_auto_20220401_1207'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='bkg_password',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='bkg_user',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='regionalstatistik_password',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='regionalstatistik_user',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]