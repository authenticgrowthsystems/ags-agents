-- 023: metryki poziomu KANALU (koniec slepoty metrycznej - plan dnia 19/07 krok [1]).
-- Zrodla: import xlsx AggregateAnalytics LinkedIn (Telegram -> /metrics/xlsx), reczny wpis X,
-- w przyszlosci kolektor X (wytrych po researchu RESEARCH_X_METRICS_*). Per-post metryki
-- zostaja w published_posts.engagement_metrics (jsonb, merge ||) - to juz istnieje.

CREATE TABLE IF NOT EXISTS channel_metrics_daily (
    id BIGSERIAL PRIMARY KEY,
    brand_id VARCHAR(50) NOT NULL,
    channel VARCHAR(40) NOT NULL,
    metric_date DATE NOT NULL,
    impressions INT,
    reactions INT,
    new_followers INT,
    followers_total INT,
    source VARCHAR(30) NOT NULL DEFAULT 'linkedin_xlsx'
      CHECK (source IN ('linkedin_xlsx', 'x_manual', 'x_api', 'linkedin_api')),
    raw JSONB,
    imported_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (brand_id, channel, metric_date)
);
CREATE INDEX IF NOT EXISTS idx_chan_metrics_lookup ON channel_metrics_daily(brand_id, channel, metric_date DESC);

-- Demografia obserwujacych: snapshot per import (lokalizacja/wielkosc firmy/stanowisko itd.)
CREATE TABLE IF NOT EXISTS channel_audience_snapshots (
    id BIGSERIAL PRIMARY KEY,
    brand_id VARCHAR(50) NOT NULL,
    channel VARCHAR(40) NOT NULL,
    captured_date DATE NOT NULL,
    followers_total INT,
    demographics JSONB NOT NULL,
    source VARCHAR(30) NOT NULL DEFAULT 'linkedin_xlsx',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (brand_id, channel, captured_date)
);

-- Kontrola
SELECT 'channel_metrics_daily' AS co, COUNT(*)::text AS n FROM channel_metrics_daily
UNION ALL
SELECT 'channel_audience_snapshots', COUNT(*)::text FROM channel_audience_snapshots;
