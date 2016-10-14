# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-14 03:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0013_auto_20161013_2019'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='user',
            new_name='created_by',
        ),
        migrations.AddField(
            model_name='comment',
            name='routine',
            field=models.ForeignKey(default='15', on_delete=django.db.models.deletion.CASCADE, to='workouts.Routine'),
            preserve_default=False,
        ),
    ]