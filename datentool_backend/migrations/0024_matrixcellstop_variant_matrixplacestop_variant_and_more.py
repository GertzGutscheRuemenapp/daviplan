# Generated by Django 4.1.1 on 2022-11-08 20:27

import datentool_backend.indicators.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datentool_backend', '0023_alter_matrixcellplace_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='matrixcellstop',
            name='variant',
            field=models.ForeignKey(default=datentool_backend.modes.models.get_default_transit_variant, on_delete=django.db.models.deletion.CASCADE, to='datentool_backend.modevariant'),
        ),
        migrations.AddField(
            model_name='matrixplacestop',
            name='variant',
            field=models.ForeignKey(default=datentool_backend.modes.models.get_default_access_variant, on_delete=django.db.models.deletion.CASCADE, to='datentool_backend.modevariant'),
        ),
        migrations.AlterUniqueTogether(
            name='matrixcellstop',
            unique_together={('variant', 'access_variant', 'cell', 'stop')},
        ),
        migrations.AlterUniqueTogether(
            name='matrixplacestop',
            unique_together={('variant', 'access_variant', 'place', 'stop')},
        ),
    ]
