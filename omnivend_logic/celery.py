import os
from celery import Celery
from celery.schedules import crontab
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omnivend_logic.settings')

app = Celery('omnivend_logic')

# Load task modules from all registered Django apps
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    # Daily aggregation task at midnight
    "daily-aggregations": {
        "task": "inventory.tasks.run_daily_aggregations",  # your task path
        "schedule": crontab(hour=0, minute=0),
    },
}
app.conf.timezone = "GMT"