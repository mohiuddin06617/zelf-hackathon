import requests
from django.conf import settings

from contentapi.celery import app
from contentapi.settings import (
    CELERY_TASK_PULL_API_URL,
    CELERY_TASK_STORE_API_URL,
)
from contents.models import Content
from contents.utils import ContentFetcher


def pull_and_store_content():
    res = requests.get(CELERY_TASK_PULL_API_URL).json()
    for item in res:
        payload = {**item}
        requests.post(CELERY_TASK_STORE_API_URL, json=payload)

@app.task(queue="contentapi.content_pull")
def pull_and_store_content():
    # TODO: The design of this celery task is very weird. It's posting the response to localhost:3000.
    #  which is not ideal

    fetcher = ContentFetcher()
    fetcher.fetch_contents()
