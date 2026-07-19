"""R5 content memory: archiwum publikacji cross-channel (published_posts) + podobienstwo semantyczne
(pgvector + OpenAI text-embedding-3-small, klucz z app_secrets) + sugestie adaptacji starej tresci na nowy
kanal. Wzorzec Centralized Content Brain: reuse tresci = fundament. Embeddingi liczone leniwie (backfill
przy zapytaniu), koszt pomijalny ($0.02/1M tokenow)."""
import json

import httpx

from . import db
from .brand import load_brand
from . import generate

EMBED_MODEL = "text-embedding-3-small"  # 1536 wymiarow, zgodne z published_posts.embedding vector(1536)


def _vec_literal(v):
    return "[" + ",".join(f"{x:.7f}" for x in v) + "]"


def embed(text):
    """Embedding tekstu przez OpenAI (klucz z app_secrets). None gdy brak klucza/blad - degradacja bez crashy."""
    key = db.get_secret("openai_api_key")
    if not key or not (text or "").strip():
        return None
    try:
        r = httpx.post("https://api.openai.com/v1/embeddings",
                       headers={"Authorization": f"Bearer {key}"},
                       json={"model": EMBED_MODEL, "input": text[:8000]}, timeout=30)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]
    except Exception:
        return None


def _backfill_embeddings(brand_id, limit=25):
    """Leniwe uzupelnianie embeddingow archiwum (per wywolanie find_similar, malymi porcjami)."""
    rows = db.fetchall(
        "SELECT id, content FROM published_posts WHERE brand=%s AND embedding IS NULL AND content <> '' ORDER BY id DESC LIMIT %s",
        (brand_id, limit),
    )
    for r in rows:
        v = embed(r["content"])
        if v is None:
            break  # brak klucza/blad: nie mlocic API w petli
        db.execute("UPDATE published_posts SET embedding = %s::vector WHERE id=%s", (_vec_literal(v), r["id"]))


def get_published(brand_id, days_ago=90, channel=None, limit=50):
    q = """SELECT id, platform, content, topic, post_url, published_at, engagement_metrics
           FROM published_posts WHERE brand=%s AND published_at > NOW() - make_interval(days => %s)"""
    params = [brand_id, days_ago]
    if channel:
        q += " AND platform=%s"
        params.append(channel)
    q += " ORDER BY published_at DESC LIMIT %s"
    params.append(limit)
    return db.fetchall(q, params)


def top_performing(brand_id, channel=None, metric="engagement", top_n=10, days_ago=90):
    """Top posty wg metryki z engagement_metrics (JSONB); bez metryk sortuje po swiezosci (NULLS LAST)."""
    q = """SELECT id, platform, content, topic, post_url, published_at,
                  (engagement_metrics->>%s)::numeric AS metric_value
           FROM published_posts WHERE brand=%s AND published_at > NOW() - make_interval(days => %s)"""
    params = [metric, brand_id, days_ago]
    if channel:
        q += " AND platform=%s"
        params.append(channel)
    q += " ORDER BY (engagement_metrics->>%s)::numeric DESC NULLS LAST, published_at DESC LIMIT %s"
    params.extend([metric, top_n])
    return db.fetchall(q, params)


def find_similar(text, brand_id="AGS", top_n=5):
    """Podobienstwo semantyczne do archiwum (pgvector cosine). Zwraca [(row, similarity)]."""
    _backfill_embeddings(brand_id)
    qv = embed(text)
    if qv is None:
        return []
    rows = db.fetchall(
        """SELECT id, platform, content, topic, post_url, published_at,
                  1 - (embedding <=> %s::vector) AS similarity
           FROM published_posts WHERE brand=%s AND embedding IS NOT NULL
           ORDER BY embedding <=> %s::vector LIMIT %s""",
        (_vec_literal(qv), brand_id, _vec_literal(qv), top_n),
    )
    return rows


DUP_THRESHOLD = 0.85  # cosine; strojenie bez rebuilda przez brand_config['cm_dup_threshold']
DUP_WINDOW_DAYS = 30  # brief 14-30: szersze okno lapie wiecej, koszt embeddingu pomijalny


def _dup_threshold(brand_id="AGS"):
    row = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id=%s AND config_key='cm_dup_threshold' ORDER BY version DESC LIMIT 1",
        (brand_id,))
    try:
        return float((row or {}).get("config_value"))
    except (TypeError, ValueError):
        return DUP_THRESHOLD


def dup_check(text, brand_id="AGS", days=DUP_WINDOW_DAYS, threshold=None):
    """BRAMKA DUPLIKACJI (kanon 19/07): porownuje canonicala z OPUBLIKOWANYMI z ostatnich `days` dni
    (pgvector cosine). NIE blokuje - tylko INFORMUJE. Zwraca dict najlepszego trafienia >= progu albo None.
    Degradacja bez crashy: brak klucza/embeddingu/dopasowania -> None (material idzie dalej bez ostrzezenia).
    Osobna od find_similar, bo filtruje po dacie publikacji (find_similar ignoruje date)."""
    if threshold is None:
        threshold = _dup_threshold(brand_id)
    _backfill_embeddings(brand_id)
    qv = embed(text)
    if qv is None:
        return None
    row = db.fetchone(
        """SELECT platform, content, topic, post_url, published_at,
                  1 - (embedding <=> %s::vector) AS similarity
           FROM published_posts
           WHERE brand=%s AND embedding IS NOT NULL
             AND published_at > NOW() - make_interval(days => %s)
           ORDER BY embedding <=> %s::vector LIMIT 1""",
        (_vec_literal(qv), brand_id, days, _vec_literal(qv)),
    )
    if not row or row.get("similarity") is None or float(row["similarity"]) < threshold:
        return None
    return row


def dup_warning_text(hit):
    """Formatuje descriptor ostrzezenia dla content_items.media (kind='dup_warning'). Czysta funkcja
    (bez DB/API) - testowalna lokalnie. `hit` = wiersz z dup_check()."""
    if not hit:
        return None
    head = (hit.get("content") or "").strip().replace("\n", " ")[:80]
    sim = float(hit.get("similarity") or 0)
    plat = hit.get("platform") or "?"
    when = ""
    pa = hit.get("published_at")
    if pa is not None:
        try:
            when = f", {pa.strftime('%d/%m')}"
        except Exception:
            when = ""
    return f'podobienstwo {sim:.2f} do "{head}" [{plat}{when}]'


def suggest_adaptation(published_id, target_channel, brand_id="AGS"):
    """Propozycja adaptacji opublikowanego posta na inny kanal (tier 'variant' z routera R4).
    Zwraca tekst propozycji; do kolejki trafia dopiero przez propose_material + approve Tomasza."""
    row = db.fetchone("SELECT content, platform FROM published_posts WHERE id=%s AND brand=%s",
                      (published_id, brand_id))
    if not row or not (row.get("content") or "").strip():
        return None, None
    brand = load_brand(brand_id)
    text, _ = generate.generate_variant(brand, row["content"], target_channel)
    return text, row["platform"]


def adaptation_candidates_note(brand_id, new_channel, top_n=5):
    """Tekst propozycji dla Tomasza przy aktywacji nowego kanalu (hook open/closed)."""
    top = top_performing(brand_id, top_n=top_n)
    if not top:
        return None
    lines = [f"Nowy kanal aktywny: {new_channel} ({brand_id}). Kandydaci do adaptacji z archiwum:"]
    for t in top:
        mv = f" | metryka: {t['metric_value']}" if t.get("metric_value") is not None else ""
        lines.append(f"- #{t['id']} [{t['platform']}] {(t['content'] or '')[:70]}{mv}")
    lines.append(f"Napisz do CM: \"adaptuj #<id> na {new_channel}\" albo poproc o inny wybor.")
    return "\n".join(lines)
