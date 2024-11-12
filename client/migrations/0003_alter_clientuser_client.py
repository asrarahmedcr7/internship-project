# Generated by Django 5.1.2 on 2024-11-12 10:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0002_alter_clientuser_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientuser',
            name='client',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='ClientUsers', to='client.client'),
            preserve_default=False,
        ),
    ]
