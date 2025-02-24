import logging
from datetime import timezone, timedelta, datetime

import requests

import libs.env as env


class WebhookHandler(logging.Handler):
    def __init__(self, url):
        super().__init__()
        self.url = url

    def emit(self, record: logging.LogRecord):
        data = {
            "content": self.format(record),
        }
        params = {"thread_id": env.LOGGING_CHANNEL_ID}
        res = requests.post(url=self.url, json=data, params=params)


class DatetimeFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt=None):
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S,%03d"

        TZ_JST = timezone(timedelta(hours=+9), 'JST')
        created_time = datetime.fromtimestamp(record.created, tz=TZ_JST)
        s = created_time.strftime(datefmt)

        return s
