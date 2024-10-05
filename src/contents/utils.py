import time

import requests

from contentapi import settings
from contents.models import Content, Author


class ContentFetcher:
    def __init__(self):
        self.API_BASE_URL = settings.API_BASE_URL
        self.header_api_key = settings.CONTENT_API_HEADER_X_API_KEY

    def fetch_contents(self):
        page_number = 1
        while page_number:
            page_number = self.get_content_page(page_number)
            if not page_number:
                break
            print(f"Processed page {page_number}")

    def get_content_page(self, page_number):
        url = f'{self.API_BASE_URL}/api/v1/contents?page={page_number}'
        response = self.make_api_request(url)

        if response:
            self.process_content_data(response)
            return response.get('next')
        return None

    def make_api_request(self, url):

        headers = {'x-api-key': self.header_api_key}

        while True:
            response = requests.get(url, headers=headers)

            if response.ok:
                return response.json()

            response_data = response.json()
            if response_data.get('code') == 401:
                print("Request limit exceeded, sleeping for 5 seconds")
                time.sleep(5)
            elif response_data.get('code') in [419, 402]:
                print("Something went wrong, retrying")
            else:
                print(f"Unexpected error: {response_data}")
                return None

    def process_content_data(self, response_data):
        for content_data in response_data['data']:
            self.process_single_content(content_data)

    def process_single_content(self, content_data):
        try:
            content_unique_id = content_data['unq_external_id']
            author = self.process_author(content_data.get('author'))
            thumbnail_url = content_data['thumbnail_view_url']
            title = content_data['title']
        except KeyError as e:
            print(f"Missing key in content data: {e}")
            return
        except Exception as e:
            print(f"Error processing content: {e}")
            return

        content, created = Content.objects.get_or_create(
            unique_id=content_unique_id,
            defaults={
                'author': author,
                'url': thumbnail_url,
                'title': title,
                'data': content_data  # Presuming data field exists in content
            }
        )
        self.update_content_if_needed(content, content_data, created)

    def process_author(self, author_data):
        if not author_data:
            return None

        author, _ = Author.objects.get_or_create(
            unique_id=author_data['unique_name'],
            defaults={
                'name': author_data.get('full_name'),
                'url': author_data.get('url'),
                'metadata': author_data.get('big_metadata'),  # Assuming a metadata field
                'secret': author_data.get('secret_value')  # Assuming a secret field
            }
        )
        return author

    def update_content_if_needed(self, content, new_data, created):
        if created:
            print("New content created")
            content.data = new_data
            content.save()
        elif content.data != new_data:
            print("Content data updated")
            content.data = new_data
            content.save()
        else:
            print("Content data not updated, continuing")


from contents.models import Content, Comment

logger = logging.getLogger(__name__)


class ContentPusher:
    def __init__(self):
        self.generate_comment_url = "https://hackapi.hellozelf.com/api/v1/ai_comment/"
        self.post_comment_url = "https://hackapi.hellozelf.com/api/v1/comment/"
        self.api_key = settings.CONTENT_API_HEADER_X_API_KEY

    def push(self):
        while True:
            content = Content.objects.filter(is_pushed=False).first()
            if content:
                self.handle_comment_posting(content)
            else:
                logger.info("No content available to push.")
            time.sleep(30)  # Wait 30 seconds between each push to respect rate limits

    def handle_comment_posting(self, content):
        response = self.generate_comment(content)

        if response and response.status_code == 200:
            comment_data = response.json()
            self.post_comment(content, comment_data)
        else:
            logger.error(f"Comment Generation Failed: {response}")

    def generate_comment(self, content):
        data = {
            "content_id": content.unique_id,
            "title": content.title,
            "url": content.url,
            "author_username": content.author.username,
        }
        for _ in range(3):  # Retry mechanism
            try:
                response = requests.post(
                    self.generate_comment_url,
                    headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
                    json=data,
                )
                if response.ok:
                    logger.info(f"AI Comment generated successfully for content {content.unique_id}")
                    return response
                logger.warning(f"Failed to generate AI comment: {response.json()}")
            except requests.RequestException as e:
                logger.error(f"Request exception: {e}")
            time.sleep(5)

        logger.error("Failed to generate AI comment after retries")
        return None

    def post_comment(self, content, comment_data):
        data = {
            "content_id": content.unique_id,
            "comment_text": comment_data.get("comment_text"),
        }
        for _ in range(3):  # Retry mechanism
            try:
                response = requests.post(
                    self.post_comment_url,
                    headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
                    json=data,
                )
                if response.status_code == 201:
                    content.is_pushed = True
                    content.save()
                    self.save_comment_data(comment_data, content)
                    logger.info(f"Comment successfully posted for content {content.unique_id}")
                    return
                elif (
                        response.status_code == 400
                        and "This content is not available for commenting" in response.json().get("error", "")
                ):
                    logger.warning("This content is not available for commenting, skipping")
                    return
                logger.warning(f"Failed to post comment: {response.json()}")
            except requests.RequestException as e:
                logger.error(f"Request exception: {e}")
            time.sleep(5)

        logger.error("Failed to post comment after retries")

    def save_comment_data(self, comment_data, content):
        Comment.objects.create(
            unique_id=comment_data['id'],
            content=content,
            text=comment_data['comment_text'],
            posted=True,
            data=comment_data
        )