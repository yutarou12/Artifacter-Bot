import logging
import requests


class WebhookHandler(logging.Handler):
    def __init__(self, url):
        super().__init__()
        self.url = url

    def emit(self, record: logging.LogRecord):
        data = {
            "content": self.format(record),
            "username": "Bot Log",
        }
        res = requests.post(url=self.url, json=data)
