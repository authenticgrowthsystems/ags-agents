# -*- coding: utf-8 -*-
"""Jednorazowa HURTOWA korekta polszczyzny kolejki (polecenie Tomasza 06/07: 'wycofaj wszystkie
karty, popraw polszczyzne' - zamiast klikania po jednej). Przepuszcza przez filtr polish_pl:
- master_theme wszystkich draft/needs_approval/planned/proposed (tematy-matki, w tym propozycje luk),
- canonical_body wszystkich needs_approval (to czyta Tomasz na kartach),
- polskie warianty w post_queue 'review'/'held' (EN nietkniete - heurystyka looks_polish).
Uruchomienie (Mikrus):
  docker run --rm --network n8n_network --env-file cm-agent/.env cm-agent:latest python -m app.bulk_polish
"""
from . import db, compliance


def main():
    fixed_theme = fixed_body = fixed_var = 0
    items = db.fetchall(
        """SELECT id, master_theme, canonical_body, status FROM content_items
           WHERE brand_id='AGS' AND status IN ('draft','needs_approval','planned','proposed')""")
    print(f"[polish] materialow do przegladu: {len(items)}", flush=True)
    for it in items:
        theme = it.get("master_theme") or ""
        if compliance.looks_polish(theme):
            new = compliance.polish_pl(theme, it["id"])
            if new.strip() and new.strip() != theme.strip():
                db.execute("UPDATE content_items SET master_theme=%s, updated_at=NOW() WHERE id=%s",
                           (new.strip(), it["id"]))
                fixed_theme += 1
        body = it.get("canonical_body") or ""
        if it["status"] == "needs_approval" and compliance.looks_polish(body):
            new = compliance.polish_pl(body, it["id"])
            if new.strip() and new.strip() != body.strip():
                db.execute("UPDATE content_items SET canonical_body=%s, updated_at=NOW() WHERE id=%s",
                           (new.strip(), it["id"]))
                fixed_body += 1
        print(f"  ok {str(it['id'])[:8]} [{it['status']}]", flush=True)
    rows = db.fetchall("SELECT id, content FROM post_queue WHERE status IN ('review','held')")
    print(f"[polish] wariantow w kolejce: {len(rows)}", flush=True)
    for r in rows:
        c = r.get("content") or ""
        if compliance.looks_polish(c):
            new = compliance.polish_pl(c)
            if new.strip() and new.strip() != c.strip():
                db.execute("UPDATE post_queue SET content=%s WHERE id=%s", (new.strip(), r["id"]))
                fixed_var += 1
    print(f"[polish] DONE: tematy poprawione={fixed_theme}, teksty-matki={fixed_body}, "
          f"warianty PL={fixed_var}", flush=True)


if __name__ == "__main__":
    main()
