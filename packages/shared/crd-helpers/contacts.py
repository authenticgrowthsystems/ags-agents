"""Contact CRUD operations for AGS CRD."""
import logging
import re
from typing import Optional
from .client import get_connection, CRDError

logger = logging.getLogger(__name__)


def _normalize_x_handle(handle: str) -> str:
    return handle.lstrip('@').lower().strip()


def _normalize_linkedin_url(url: str) -> str:
    url = url.strip().rstrip('/')
    match = re.search(r'linkedin\.com/in/([^/]+)', url)
    return match.group(0) if match else url


def get_contact_by_handle(platform: str, handle: str) -> Optional[dict]:
    """Find contact by social handle. platform: 'x', 'linkedin', 'instagram'."""
    field_map = {'x': 'x_handle', 'linkedin': 'linkedin_url', 'instagram': 'instagram_handle'}
    if platform not in field_map:
        raise CRDError(f"Unknown platform: {platform}")
    field = field_map[platform]
    if platform == 'x':
        normalized = _normalize_x_handle(handle)
    elif platform == 'linkedin':
        normalized = _normalize_linkedin_url(handle)
    else:
        normalized = handle.lstrip('@').lower()
    conn = get_connection()
    try:
        cur = conn.cursor()
        if platform == 'linkedin':
            cur.execute(
                f"SELECT * FROM contacts WHERE {field} ILIKE %s LIMIT 1",
                (f'%{normalized}%',)
            )
        else:
            cur.execute(
                f"SELECT * FROM contacts WHERE LOWER({field}) = %s LIMIT 1",
                (normalized,)
            )
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        raise CRDError(f"get_contact_by_handle failed: {e}")
    finally:
        conn.close()


def get_contact_by_id(contact_id: str) -> Optional[dict]:
    """Get contact by UUID."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM contacts WHERE id = %s", (contact_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        raise CRDError(f"get_contact_by_id failed: {e}")
    finally:
        conn.close()


def create_contact(data: dict) -> str:
    """Create new contact. Returns UUID string."""
    import re as _re
    slug = _re.sub(r'[^a-z0-9]+', '_', data.get('name', 'unknown').lower()).strip('_')
    data = {**data, 'slug': slug}
    allowed = [
        'name', 'slug', 'linkedin_url', 'x_handle', 'instagram_handle',
        'facebook_url', 'email', 'phone', 'website', 'brand_affinity',
        'icp_tier', 'status', 'source', 'languages', 'geography',
        'pain_point', 'interests', 'narration', 'first_contact_date',
        'last_interaction_date', 'last_interaction_type', 'next_action',
        'next_action_due', 'next_action_owner', 'priority'
    ]
    filtered = {k: v for k, v in data.items() if k in allowed}
    cols = ', '.join(filtered.keys())
    placeholders = ', '.join(['%s'] * len(filtered))
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO contacts ({cols}) VALUES ({placeholders}) RETURNING id",
            list(filtered.values())
        )
        conn.commit()
        return str(cur.fetchone()['id'])
    except Exception as e:
        conn.rollback()
        raise CRDError(f"create_contact failed: {e}")
    finally:
        conn.close()


def update_contact(contact_id: str, updates: dict) -> bool:
    """Update contact fields. Returns True if found and updated."""
    if not updates:
        return False
    allowed = [
        'name', 'linkedin_url', 'x_handle', 'instagram_handle',
        'facebook_url', 'email', 'phone', 'website', 'brand_affinity',
        'icp_tier', 'status', 'source', 'languages', 'geography',
        'pain_point', 'interests', 'narration', 'first_contact_date',
        'last_interaction_date', 'last_interaction_type', 'next_action',
        'next_action_due', 'next_action_owner', 'priority'
    ]
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        return False
    set_clause = ', '.join([f"{k} = %s" for k in filtered.keys()])
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE contacts SET {set_clause} WHERE id = %s",
            list(filtered.values()) + [contact_id]
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise CRDError(f"update_contact failed: {e}")
    finally:
        conn.close()


def update_contact_status(contact_id: str, new_status: str) -> bool:
    """Update contact status field."""
    valid = ['Cold', 'Warm', 'Hot', 'Customer', 'Ghosted', 'Peer', 'Competitor']
    if new_status not in valid:
        raise CRDError(f"Invalid status: {new_status}. Must be one of {valid}")
    return update_contact(contact_id, {'status': new_status})


def search_contacts(query: str, limit: int = 10) -> list:
    """Search contacts by name, x_handle, or email."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        like = f'%{query}%'
        cur.execute(
            "SELECT * FROM contacts WHERE name ILIKE %s OR x_handle ILIKE %s OR email ILIKE %s "
            "ORDER BY last_interaction_date DESC NULLS LAST LIMIT %s",
            (like, like, like, limit)
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        raise CRDError(f"search_contacts failed: {e}")
    finally:
        conn.close()
