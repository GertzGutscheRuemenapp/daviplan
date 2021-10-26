# Generated by Django 3.2.8 on 2021-10-26 13:08

import datentool_backend.base
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datentool_backend', '0016_rename_raster_rastercellpopulationagegender_disaggraster'),
    ]

    operations = [
        migrations.CreateModel(
            name='DemandRateSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('is_default', models.BooleanField()),
                ('age_classification', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='datentool_backend.ageclassification')),
            ],
            bases=(datentool_backend.base.NamedModel, models.Model),
        ),
        migrations.CreateModel(
            name='DemandRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('age_group', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='datentool_backend.agegroup')),
                ('demand_rate_set', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='datentool_backend.demandrateset')),
                ('year', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='datentool_backend.year')),
            ],
        ),
    ]
