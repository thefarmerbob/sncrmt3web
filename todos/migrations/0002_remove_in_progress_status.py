# Generated by Django 5.2 on 2025-05-25 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompletedTodo',
            fields=[
            ],
            options={
                'verbose_name': 'Completed Todo',
                'verbose_name_plural': 'Completed Todos',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('todos.todo',),
        ),
        migrations.AlterField(
            model_name='todo',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending', max_length=20),
        ),
    ]
