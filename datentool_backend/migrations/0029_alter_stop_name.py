# Generated by Django 4.1.4 on 2022-12-20 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datentool_backend', '0028_alter_planningprocess_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stop',
            name='name',
            field=models.TextField(blank=True),
        ),
    ]
