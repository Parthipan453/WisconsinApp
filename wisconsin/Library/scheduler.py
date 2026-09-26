from apscheduler.schedulers.background import BackgroundScheduler

from Library.due_date_notifications import check_due_date_notifications


scheduler = BackgroundScheduler()


def start():

    if scheduler.running:
        return

    scheduler.add_job(
        check_due_date_notifications,
        trigger="interval",
        minutes=1,
        id="library_due_date_notifications",
        replace_existing=True,
    )

    scheduler.start()