# Generated by Django 5.2 on 2025-05-25 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_alter_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='rejection_note',
            field=models.TextField(blank=True, help_text='Reason for rejecting the payment proof'),
        ),
    ]
