# Generated by Django 5.2 on 2025-05-26 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todos', '0005_alter_todo_coliver_name_alter_todo_task_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todo',
            name='task_type',
            field=models.CharField(choices=[('application_review', 'Application Review'), ('payment_review', 'Payment Review'), ('transfer_review', 'Transfer Review'), ('maintenance_review', 'Maintenance Review'), ('maintenance_verification', 'Maintenance Verification'), ('other', 'Other')], max_length=50),
        ),
    ]
