"""Notion CRD documentation page sync operations."""
import logging
from typing import Optional
from .client import NotionClient, NotionError
from datetime import datetime

logger = logging.getLogger(__name__)
CRD_DOC_PAGE_ID = "371c00c90b9381ec9b13c1d910c9a547"
AGS_OPS_HUB_ID = "318c00c90b9381f69449ee3f8546ca33"

def search_crd_page(name: str) -> Optional[dict]:
    """Search for a contact page in AGS Operations Hub by name."""
    client = NotionClient()
    try:
        response = client.post("/search", {"query": name, "filter": {"property": "object", "value": "page"}, "page_size": 10})
        for result in response.get('results', []):
            title_prop = result.get('properties', {}).get('title', {})
            if not title_prop:
                title = result.get('title', [])
                page_title = ''.join(t.get('plain_text', '') for t in (title if isinstance(title, list) else []))
            else:
                title_arr = title_prop.get('title', [])
                page_title = ''.join(t.get('plain_text', '') for t in title_arr)
            if name.lower() in page_title.lower():
                return result
        return None
    except NotionError as e:
        logger.error(f"search_crd_page failed for {name}: {e}")
        return None

def append_crd_log_entry(page_id: str, entry: dict) -> bool:
    """Append engagement log entry to a CRD person page."""
    client = NotionClient()
    try:
        date_str = entry.get('date', datetime.now().strftime('%Y-%m-%d'))
        channel = entry.get('channel', 'Unknown')
        action_type = entry.get('action_type', 'interaction')
        agent = entry.get('agent', 'System')
        content = entry.get('content', '')[:500]
        response_text = entry.get('response', '')
        heading_text = f"{date_str} - {channel} - {action_type}"
        blocks = [
            {"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"type": "text", "text": {"content": heading_text}}]}},
            {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": f"Agent: {agent}"}}]}},
            {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": f"Content: {content}"}}]}},
        ]
        if response_text:
            blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": f"Response: {response_text[:500]}"}}]}})
        client.patch(f"/blocks/{page_id}/children", {"children": blocks})
        return True
    except NotionError as e:
        logger.error(f"append_crd_log_entry failed for page {page_id}: {e}")
        return False

def update_crd_doc_note(note: str) -> bool:
    """Append a note to the CRD documentation page."""
    client = NotionClient()
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        block = {"object": "block", "type": "callout", "callout": {"rich_text": [{"type": "text", "text": {"content": f"[{timestamp}] {note}"}}], "icon": {"emoji": "ℹ️"}, "color": "blue_background"}}
        client.patch(f"/blocks/{CRD_DOC_PAGE_ID}/children", {"children": [block]})
        return True
    except NotionError as e:
        logger.error(f"update_crd_doc_note failed: {e}")
        return False
