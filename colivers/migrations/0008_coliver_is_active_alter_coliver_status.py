# Generated by Django 5.2 on 2025-05-25 15:25

from django.db import migrations, models

def set_default_is_active(apps, schema_editor):
    Coliver = apps.get_model('colivers', 'Coliver')
    # Set is_active=True for all existing colivers
    Coliver.objects.all().update(is_active=True)

def reverse_default_is_active(apps, schema_editor):
    pass  # No need to do anything when reversing

class Migration(migrations.Migration):

    dependencies = [
        ('colivers', '0007_activecoliver_archivedcoliver'),
    ]

    operations = [
        migrations.AddField(
            model_name='coliver',
            name='is_active',
            field=models.BooleanField(default=True, help_text='If unchecked, the coliver will be moved to the archive.'),
        ),
        migrations.AlterField(
            model_name='coliver',
            name='status',
            field=models.CharField(choices=[('ONBOARDING', 'Onboarding'), ('COLIVING', 'Coliving'), ('APPLICATION', 'Application')], default='ONBOARDING', max_length=20),
        ),
        migrations.RunPython(set_default_is_active, reverse_default_is_active),
    ]
