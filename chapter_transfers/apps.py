from django.apps import AppConfig


class ChapterTransfersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chapter_transfers'
    verbose_name = 'Chapter Transfers'

    def ready(self):
        import chapter_transfers.signals  # Import signals when app is ready
