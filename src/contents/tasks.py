import requests
from django.conf import settings

from contentapi.celery import app
from contents.utils import ContentFetcher, ContentPusher


@app.task(queue="contentapi.content_pull")
def pull_and_store_content():
    # TODO: The design of this celery task is very weird. It's posting the response to localhost:3000.
    #  which is not ideal

    fetcher = ContentFetcher()
    fetcher.fetch_contents()

@app.task(queue="contentapi.push_content")
def content_pusher():
    content_pusher = ContentPusher()
    content_pusher.push()
