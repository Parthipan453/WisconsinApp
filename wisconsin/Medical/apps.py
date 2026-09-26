""" Dominic Code """
import os
import sys
import logging

from django.apps import AppConfig
    
logger = logging.getLogger(__name__)


class MedicalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Medical'

    def ready(self):
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        management_commands_to_skip = {
            'makemigrations', 'migrate', 'shell', 'shell_plus', 'collectstatic',
            'test', 'createsuperuser', 'dumpdata', 'loaddata', 'generate_vapid_keys','reset_db',
        }
        if len(sys.argv) > 1 and sys.argv[1] in management_commands_to_skip:
            return

        from apscheduler.schedulers.background import BackgroundScheduler

        def _run_reminder_sweep():
            from Medical.Dominic.reminders import fire_due_reminders_for_all
            try:
                fire_due_reminders_for_all()
            except Exception:
                logger.exception("Scheduled reminder sweep crashed")

        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            _run_reminder_sweep,
            'interval',
            seconds=60,
            id='medical_due_reminders_sweep',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        logger.info("Medical: reminder background scheduler started (every 60s).")
