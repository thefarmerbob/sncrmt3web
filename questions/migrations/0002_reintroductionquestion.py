# Generated by Django 5.2 on 2025-05-27 02:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReintroductionQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Question Text')),
                ('description', models.TextField(blank=True, help_text='Additional explanatory text for the question', verbose_name='Question Description')),
                ('question_type', models.CharField(choices=[('text', 'Text Answer'), ('multiple_choice', 'Multiple Choice'), ('information', 'Information Display')], default='text', help_text='Type of question (text or multiple choice)', max_length=20)),
                ('choices', models.JSONField(blank=True, help_text="List of choices for multiple choice questions. Format: [{'text': 'Choice 1'}, {'text': 'Choice 2'}]", null=True)),
                ('order', models.PositiveIntegerField(default=0, help_text='Order in which the question appears in the reintroduction form')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this question is currently active and should be shown in the reintroduction form')),
                ('required', models.BooleanField(default=True, help_text='Whether this question is required to be answered')),
            ],
            options={
                'verbose_name': 'Reintroduction Question',
                'verbose_name_plural': 'Reintroduction Questions',
                'ordering': ['order'],
            },
        ),
    ]
