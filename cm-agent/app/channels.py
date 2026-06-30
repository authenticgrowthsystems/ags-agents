"""Generic channel connector: stage per-channel variants into post_queue (the outbox) and, on approval,
move them to their publish state per the channel's publish_mode. New channel = a registry row + (for webhook
mode) an adapter; the CM core does not change. NOTE: post_queue column set assumed from the live schema -
confirm with \\d post_queue before first run (content, brand, platform, topic, status, scheduled_for, content_item_id)."""
from . import db, config


def active_targets(brand_id, target_channels):
    """Registry rows for the item's target channels that should receive a variant now (active or draft).
    'ready' channels are scaffolded slots, skipped until activated."""
    rows = db.fetchall(
        "SELECT channel, status, adapter_path, config FROM channels WHERE brand_id=%s AND channel = ANY(%s)",
        (brand_id, list(target_channels or [])),
    )
    return [r for r in rows if r["status"] in ("active", "draft")]


def stage_variant(item, channel_row, variant_text):
    """Eager staging: write the variant as a post_queue row in 'review' (shown at the HITL gate)."""
    row = db.fetchone(
        """INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for)
           VALUES (%s,%s,%s,%s,'review',%s,%s) RETURNING id""",
        (variant_text, item["brand_id"], channel_row["channel"], item.get("master_theme"),
         item["id"], item.get("scheduled_for")),
    )
    return row["id"] if row else None


def dispatch_item(item):
    """On approval: move this item's staged 'review' rows to their publish state by channel publish_mode.
    post_queue mode -> 'scheduled' (existing per-minute Scheduler publishes, e.g. X);
    draft mode -> 'held' (Tomasz posts manually, e.g. LinkedIn); webhook mode -> 'queued' (adapter wired later)."""
    rows = db.fetchall(
        """SELECT pq.id, pq.platform, c.config
           FROM post_queue pq JOIN channels c ON c.brand_id=pq.brand AND c.channel=pq.platform
           WHERE pq.content_item_id=%s AND pq.status='review'""",
        (item["id"],),
    )
    for r in rows:
        mode = (r.get("config") or {}).get("publish_mode", config.PUBLISH_DRAFT)
        if mode == config.PUBLISH_POST_QUEUE:
            db.execute("UPDATE post_queue SET status='scheduled', scheduled_for=COALESCE(scheduled_for, NOW()) WHERE id=%s", (r["id"],))
        elif mode == config.PUBLISH_WEBHOOK:
            db.execute("UPDATE post_queue SET status='queued' WHERE id=%s", (r["id"],))
        else:
            db.execute("UPDATE post_queue SET status='held' WHERE id=%s", (r["id"],))
    return len(rows)
