"""Notion API client."""
import os, requests, logging, time
from typing import Optional

logger = logging.getLogger(__name__)
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

class NotionError(Exception):
    pass

class NotionClient:
    def __init__(self):
        token = os.environ.get('NOTION_API_TOKEN')
        if not token:
            raise NotionError("NOTION_API_TOKEN environment variable not set")
        self.headers = {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION, "Content-Type": "application/json"}

    def _handle_response(self, response):
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            logger.warning(f"Notion rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            return None
        if not response.ok:
            raise NotionError(f"Notion API error {response.status_code}: {response.text[:200]}")
        return response.json()

    def get(self, path: str, params: dict = None) -> dict:
        for attempt in range(3):
            r = requests.get(f"{BASE_URL}{path}", headers=self.headers, params=params, timeout=30)
            result = self._handle_response(r)
            if result is not None:
                return result
        raise NotionError("Notion API rate limit exceeded after 3 retries")

    def post(self, path: str, data: dict) -> dict:
        r = requests.post(f"{BASE_URL}{path}", headers=self.headers, json=data, timeout=30)
        return self._handle_response(r)

    def patch(self, path: str, data: dict) -> dict:
        r = requests.patch(f"{BASE_URL}{path}", headers=self.headers, json=data, timeout=30)
        return self._handle_response(r)
