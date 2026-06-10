# CRD Helpers

PostgreSQL CRD operations for AGS X Agent.

## Setup

```
pip install psycopg2-binary
```

Environment variables required:

- `CRD_PASSWORD` (required)
- `CRD_HOST` (default: pg_n8n)
- `CRD_PORT` (default: 5432)
- `CRD_DATABASE` (default: ags_crd)
- `CRD_USER` (default: ags_crd_user)

## Quick usage

### Contacts

```python
from crd_helpers import get_contact_by_handle, get_contact_by_id, create_contact, update_contact, update_contact_status, search_contacts

# Look up by X handle (@ prefix stripped automatically)
contact = get_contact_by_handle('x', '@naval')

# Look up by UUID
contact = get_contact_by_id('b3f1a2c4-...')

# Create new contact (returns UUID string)
contact_id = create_contact({
    'name': 'Naval Ravikant',
    'x_handle': 'naval',
    'icp_tier': 'A',
    'status': 'Cold',
})

# Update arbitrary fields
update_contact(contact_id, {'next_action': 'Reply to thread', 'priority': 'High'})

# Update status only (validated against allowed values)
update_contact_status(contact_id, 'Warm')  # Cold/Warm/Hot/Customer/Ghosted/Peer/Competitor

# Search by name, x_handle, or email
results = search_contacts('naval', limit=5)
```

### Engagement log

```python
from crd_helpers import append_engagement, get_contact_engagements, update_engagement_metrics, count_today_posts

# Log a post (contact_id optional - pass None for broadcast posts with no linked contact)
log_id = append_engagement(contact_id, {
    'action_type': 'x_post',   # x_post / x_reply / x_comment / x_dm / email
    'channel': 'X',
    'agent': 'X Agent',
    'content': 'Thread text here...',
    'platform_id': '1234567890',  # tweet_id
    'metrics': {'impressions': 0, 'likes': 0, 'replies': 0},
})

# Get recent engagements for a contact
history = get_contact_engagements(contact_id, limit=10)

# Update metrics after polling Twitter API
update_engagement_metrics('1234567890', {'impressions': 4200, 'likes': 31, 'replies': 7})

# Rate limit check - how many posts today?
posts_today = count_today_posts(channel='X', agent='X Agent')
```

### CRDClient context manager (for multi-step transactions)

```python
from crd_helpers import CRDClient, CRDError

with CRDClient() as crd:
    crd.cursor.execute("SELECT * FROM contacts WHERE icp_tier = 'A'")
    rows = [dict(r) for r in crd.cursor.fetchall()]
# commits on exit, rolls back on exception
```

### Error handling

```python
from crd_helpers import CRDError

try:
    contact = get_contact_by_handle('x', '@someone')
except CRDError as e:
    logger.error(f"CRD operation failed: {e}")
```
