-- 025: kolektor metryk X Owned Reads (BRIEF_KOLEKTOR_METRYK_X_19072026, build build/kolektor-x).
-- Dzienne snapshoty per-post z GET /2/users/{id}/tweets (public/non_public/organic namespaces).
-- Prywatne metryki (impressions organic, url_link_clicks, user_profile_clicks) istnieja TYLKO
-- dla postow <30 dni - snapshot dzienny utrwala je zanim znikna. Konsumenci: reports.refresh_metrics
-- (stats_mode 'x_owned_reads' -> merge do published_posts.engagement_metrics, ZERO odczytow API)
-- + przyszle raporty trendow. Zbior: app/x_collector.py (tick w petli workera, raz na dobe UTC).
-- Wlaczenie celu (PO sondzie i potwierdzeniu ceny Owned Read w Developer Console - DoD):
--   UPDATE channels SET config = jsonb_set(config,'{stats_mode}','"x_owned_reads"')
--   WHERE brand_id='AGS' AND channel='x';
-- (DDL celowo NIE przelacza stats_mode - kolejnosc wlaczenia nalezy do Tomasza.)

CREATE TABLE IF NOT EXISTS x_post_metric_snapshots (
    id BIGSERIAL PRIMARY KEY,
    brand_id VARCHAR(50) NOT NULL,
    channel VARCHAR(40) NOT NULL DEFAULT 'x',
    tweet_id VARCHAR(30) NOT NULL,
    snapshot_date DATE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')::date,
    observed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at_x TIMESTAMPTZ,
    public_metrics JSONB,
    non_public_metrics JSONB,
    organic_metrics JSONB,
    raw JSONB,
    UNIQUE (tweet_id, snapshot_date)
);
CREATE INDEX IF NOT EXISTS idx_xpms_tweet ON x_post_metric_snapshots(tweet_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_xpms_brand_date ON x_post_metric_snapshots(brand_id, snapshot_date DESC);

-- Kontrola
SELECT 'x_post_metric_snapshots' AS co, COUNT(*)::text AS n FROM x_post_metric_snapshots;
