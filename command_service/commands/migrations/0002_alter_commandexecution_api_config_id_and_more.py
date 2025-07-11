# Generated by Django 4.2.21 on 2025-06-12 03:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('commands', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commandexecution',
            name='api_config_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='commandexecution',
            name='command_request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='commands.commandrequest'),
        ),
        migrations.AlterField(
            model_name='commandexecution',
            name='execution_time',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='commandexecution',
            name='response_data',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
