from django.apps import AppConfig


class ApplicantsConfig(AppConfig):
    name = "Applicants"
    verbose_name = "Applicants"

    def ready(self):
        from . import signals  # noqa: F401