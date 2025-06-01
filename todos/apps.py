from django.apps import AppConfig


class TodosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'todos'
    verbose_name = 'Admin Todo List'

    def ready(self):
        import todos.signals  # Import signals when app is ready
