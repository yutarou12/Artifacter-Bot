import os
from dotenv import load_dotenv

load_dotenv()


DISCORD_BOT_TOKEN: str = os.environ.get("DISCORD_BOT_TOKEN", "")
ON_READY_CHANNEL_ID: int = int(os.environ.get("ON_READY_CHANNEL_ID", ""))
ON_INTERACTION_CHANNEL_ID: int = int(os.environ.get("ON_INTERACTION_CHANNEL_ID", ""))
TRACEBACK_CHANNEL_ID: int = int(os.environ.get("TRACEBACK_CHANNEL_ID", ""))
ERROR_CHANNEL_ID: int = int(os.environ.get("ERROR_CHANNEL_ID", ""))

POSTGRESQL_HOST_NAME: str = os.environ.get("POSTGRESQL_HOST_NAME", "")
POSTGRESQL_USER: str = os.environ.get("POSTGRESQL_USER", "")
POSTGRESQL_PASSWORD: str = os.environ.get("POSTGRESQL_PASSWORD", "")
POSTGRESQL_DATABASE_NAME: str = os.environ.get("POSTGRESQL_DATABASE_NAME", "")
POSTGRESQL_PORT: str = os.environ.get("POSTGRESQL_PORT", "")
API_HOST_NAME: str = os.environ.get("API_HOST_NAME", "")
API_PORT: str = os.environ.get("API_PORT", "")

DEBUG: int = int(os.environ.get("DEBUG", 0))

WEBHOOK_URL: str = os.environ.get("WEBHOOK_URL", "")
