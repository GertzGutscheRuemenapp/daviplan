# Generated by Django 3.2.11 on 2022-01-31 20:55

import datentool_backend.base
import datentool_backend.utils.protect_cascade
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datentool_backend', '0066_auto_20220129_1700'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fclass',
            old_name='classification',
            new_name='ftype',
        ),
        migrations.RenameField(
            model_name='fieldtype',
            old_name='field_type',
            new_name='ftype',
        ),
        migrations.RemoveField(
            model_name='area',
            name='attributes',
        ),
        migrations.CreateModel(
            name='AreaField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('is_label', models.BooleanField(default=False)),
                ('area_level', models.ForeignKey(on_delete=datentool_backend.utils.protect_cascade.PROTECT_CASCADE, to='datentool_backend.arealevel')),
                ('field_type', models.ForeignKey(on_delete=datentool_backend.utils.protect_cascade.PROTECT_CASCADE, to='datentool_backend.fieldtype')),
            ],
            options={
                'unique_together': {('area_level', 'name')},
            },
            bases=(datentool_backend.base.DatentoolModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='AreaAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('str_value', models.TextField(null=True)),
                ('num_value', models.FloatField(null=True)),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datentool_backend.area')),
                ('class_value', models.ForeignKey(null=True, on_delete=datentool_backend.utils.protect_cascade.PROTECT_CASCADE, to='datentool_backend.fclass')),
                ('field', models.ForeignKey(on_delete=datentool_backend.utils.protect_cascade.PROTECT_CASCADE, to='datentool_backend.areafield')),
            ],
            options={
                'unique_together': {('area', 'field')},
            },
            bases=(datentool_backend.base.DatentoolModelMixin, datentool_backend.base.NamedModel, models.Model),
        ),
    ]
