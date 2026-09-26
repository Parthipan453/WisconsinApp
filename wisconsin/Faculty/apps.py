from django.apps import AppConfig


class FacultyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Faculty'

    def ready(self):
        import Faculty.Elsa_Faculty.signals 
