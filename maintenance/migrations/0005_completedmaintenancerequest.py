# Generated by Django 5.2 on 2025-05-26 20:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0004_alter_maintenancerequest_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompletedMaintenanceRequest',
            fields=[
            ],
            options={
                'verbose_name': 'Completed maintenance request',
                'verbose_name_plural': 'Completed maintenance requests',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('maintenance.maintenancerequest',),
        ),
    ]
