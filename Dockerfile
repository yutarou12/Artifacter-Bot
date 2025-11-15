FROM python:3.10-alpine

WORKDIR /app/bot
COPY requirements.txt /app/bot-requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel
RUN if [ -f /app/bot-requirements.txt ]; then python -m pip install -r /app/bot-requirements.txt; fi

ENTRYPOINT ["python", "bot.py"]