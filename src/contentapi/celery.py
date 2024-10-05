import logging
import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contentapi.settings")


app = Celery("contentapi")

app.config_from_object(settings)
app.conf.task_default_queue = app.conf.task_default_exchange = "contentapi.content_pull"
# app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_routes = {
    "*": app.conf.task_default_queue,
}

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    'pull-content-every-minute': {
        'task': 'contentapi.tasks.pull_and_store_content',
        'schedule': crontab(minute='*/1')
    },
    'post-ai-comments-every-30-seconds': {
        'task': 'contentapi.tasks.post_ai_comments',
        'schedule': 30.0,
    },
}