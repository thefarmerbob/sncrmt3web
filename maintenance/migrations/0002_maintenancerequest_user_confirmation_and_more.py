# Generated by Django 5.2 on 2025-05-26 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintenancerequest',
            name='user_confirmation',
            field=models.BooleanField(default=False, help_text='Required confirmation from the user', verbose_name='User Confirmation'),
        ),
        migrations.AlterField(
            model_name='maintenancerequest',
            name='manager_checkbox_label',
            field=models.CharField(default='I confirm this maintenance request has been reviewed and approved', help_text='This text will appear above the required checkbox', max_length=200),
        ),
    ]
