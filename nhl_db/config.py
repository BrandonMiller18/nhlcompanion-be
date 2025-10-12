import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

RECORDS_BASE = "https://records.nhl.com/site/api"
NHL_WEB_BASE = "https://api-web.nhle.com/v1"


def get_env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


