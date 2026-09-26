from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Library'
    
    def ready(self):
        # Existing signals
        import Library.signals

        # Automatic due-date notification scheduler
        from Library.scheduler import start

        start()
