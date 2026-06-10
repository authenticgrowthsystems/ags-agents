"""X Content Queue Notion page operations."""
import re, logging
from typing import Optional
from .client import NotionClient, NotionError
from datetime import datetime

logger = logging.getLogger(__name__)
X_QUEUE_PAGE_ID = "371c00c90b9381a0bc29e1dc22e5c244"

def _parse_block_text(block: dict) -> Optional[str]:
    block_type = block.get('type', '')
    if block_type in ('bulleted_list_item', 'paragraph', 'numbered_list_item'):
        rich_text = block.get(block_type, {}).get('rich_text', [])
        return ''.join(t.get('plain_text', '') for t in rich_text)
    return None

def _parse_insight(text: str, block: dict) -> dict:
    priority_match = re.search(r'\[(HIGH|MED|LOW)\]', text, re.IGNORECASE)
    topic_matches = re.findall(r'\[([^\]]+)\]', text)
    clean_text = re.sub(r'\[[^\]]*\]', '', text).strip()
    status_match = re.match(r'\[STATUS:\s*(\w+)', text)
    return {
        'id': block.get('id'),
        'text': clean_text,
        'raw_text': text,
        'priority': priority_match.group(1).upper() if priority_match else 'MED',
        'topic': ', '.join([t for t in topic_matches if t.upper() not in ('HIGH','MED','LOW')]) or 'General',
        'status': status_match.group(1).lower() if status_match else 'queued',
        'block_type': block.get('type'),
        'raw_block': block
    }

def read_x_content_queue() -> list:
    """Read all queued insights from X Content Queue Notion page."""
    client = NotionClient()
    response = client.get(f"/blocks/{X_QUEUE_PAGE_ID}/children", params={"page_size": 100})
    blocks = response.get('results', [])
    insights = []
    for block in blocks:
        text = _parse_block_text(block)
        if not text or not text.strip():
            continue
        if text.strip().startswith('//') or text.strip().startswith('#'):
            continue
        insight = _parse_insight(text, block)
        if insight['status'] not in ('published', 'rejected', 'failed', 'archived'):
            insights.append(insight)
    logger.info(f"Found {len(insights)} queued insights in X Content Queue")
    return insights

def update_queue_entry(block_id: str, status: str, metadata: dict = None) -> bool:
    """Update a queue entry block with status prefix."""
    client = NotionClient()
    try:
        block = client.get(f"/blocks/{block_id}")
        block_type = block.get('type', 'paragraph')
        rich_text = block.get(block_type, {}).get('rich_text', [])
        original_text = ''.join(t.get('plain_text', '') for t in rich_text)
        original_text = re.sub(r'^\[STATUS:[^\]]+\]\s*', '', original_text)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        meta_str = ''
        if metadata:
            if 'tweet_url' in metadata:
                meta_str = f" | {metadata['tweet_url']}"
        prefix = f"[STATUS: {status.upper()} | {timestamp}{meta_str}] "
        new_text = prefix + original_text
        update_data = {block_type: {"rich_text": [{"type": "text", "text": {"content": new_text[:2000]}}]}}
        client.patch(f"/blocks/{block_id}", update_data)
        return True
    except NotionError as e:
        logger.error(f"update_queue_entry failed for {block_id}: {e}")
        return False

def get_queue_entry_by_id(block_id: str) -> Optional[dict]:
    """Get a specific queue entry block."""
    client = NotionClient()
    try:
        block = client.get(f"/blocks/{block_id}")
        text = _parse_block_text(block)
        if text:
            return _parse_insight(text, block)
        return None
    except NotionError:
        return None
