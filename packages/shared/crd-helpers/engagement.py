"""Engagement log operations for AGS CRD."""
import json
import logging
from typing import Optional
from datetime import datetime
from .client import get_connection, CRDError

logger = logging.getLogger(__name__)


def append_engagement(contact_id: Optional[str], action_data: dict) -> str:
    """Append engagement log entry. Returns UUID. Updates contact last_interaction if contact_id provided."""
    allowed = [
        'action_type', 'channel', 'agent', 'content', 'content_url',
        'response', 'platform_id', 'metrics', 'notes'
    ]
    filtered = {k: v for k, v in action_data.items() if k in allowed}
    if 'metrics' in filtered and isinstance(filtered['metrics'], dict):
        filtered['metrics'] = json.dumps(filtered['metrics'])
    filtered_with_contact = {**({'contact_id': contact_id} if contact_id else {}), **filtered}
    cols = ', '.join(filtered_with_contact.keys())
    placeholders = ', '.join(['%s'] * len(filtered_with_contact))
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO engagement_log ({cols}) VALUES ({placeholders}) RETURNING id",
            list(filtered_with_contact.values())
        )
        new_id = str(cur.fetchone()['id'])
        if contact_id and filtered.get('action_type'):
            action_to_type = {
                'x_post': 'Post',
                'x_reply': 'Reply',
                'x_comment': 'Comment',
                'x_dm': 'DM',
                'email': 'Email'
            }
            interaction_type = action_to_type.get(filtered.get('action_type', ''), 'Other')
            cur.execute(
                "UPDATE contacts SET last_interaction_date = CURRENT_DATE, last_interaction_type = %s WHERE id = %s",
                (interaction_type, contact_id)
            )
        conn.commit()
        return new_id
    except Exception as e:
        conn.rollback()
        raise CRDError(f"append_engagement failed: {e}")
    finally:
        conn.close()


def get_contact_engagements(contact_id: str, limit: int = 20) -> list:
    """Get recent engagements for a contact, newest first."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM engagement_log WHERE contact_id = %s ORDER BY created_at DESC LIMIT %s",
            (contact_id, limit)
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        raise CRDError(f"get_contact_engagements failed: {e}")
    finally:
        conn.close()


def update_engagement_metrics(platform_id: str, metrics: dict) -> bool:
    """Update metrics JSONB for a post by platform_id (tweet_id)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE engagement_log SET metrics = %s::jsonb WHERE platform_id = %s",
            (json.dumps(metrics), platform_id)
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise CRDError(f"update_engagement_metrics failed: {e}")
    finally:
        conn.close()


def count_today_posts(channel: str = 'X', agent: str = 'X Agent') -> int:
    """Count posts published today by this agent on this channel. Used for rate limit check."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as cnt FROM engagement_log "
            "WHERE action_type = 'x_post' AND channel = %s AND agent = %s AND created_at::date = CURRENT_DATE",
            (channel, agent)
        )
        return int(cur.fetchone()['cnt'])
    except Exception as e:
        raise CRDError(f"count_today_posts failed: {e}")
    finally:
        conn.close()
