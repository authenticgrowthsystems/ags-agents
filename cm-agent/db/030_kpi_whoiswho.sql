-- 030 (24/07/2026): paczka #1 Managera, punkty 1 + 5 + 7 w JEDNYM pliku.
-- Wykonac PRZED rebuildem cm-agent (kod po rebuildzie od razu oczekuje tych obiektow).
--
-- pkt 1: channel_kpi_snapshots - liczby z panelu analitycznego, ktore WIDZI czat na
--        abonamencie, a serwer nie (LinkedIn do czasu App 2 CMA, X poza zakupionymi
--        odczytami). Droga: [RAPORT PRACY v1] linia 'kpi_snapshot' -> parser bez LLM.
--        DLACZEGO OSOBNA TABELA, a nie channel_metrics_daily (023): tamta ma klucz
--        (brand, kanal, DATA) i zna wylacznie serie DZIENNE z importu xlsx/API. Tutaj
--        wchodza takze okresy zbiorcze (7d/28d/90d) przepisane recznie - wrzucenie
--        sumy tygodniowej do wiersza dziennego zafalszowaloby istniejaca serie.
--        Zrodlo jest jawne w kolumnie source, wiec raport zawsze wie, skad ma liczbe.
--
-- pkt 5: contacts.who_is_who JSONB - mapa "kto jest kim" po stronie KLIENTA (rola,
--        wplyw na decyzje, skad to wiemy). Sonda 24/07 potwierdzila, ze kolumny nie ma.
--        Kanon WHO IS WHO (22/07) zostaje nietkniety: 'handles' = tozsamosc per kanal,
--        'who_is_who' = pozycja czlowieka w organizacji prospekta.
--
-- pkt 7: fail-closed przed wykluczeniem z lejka. Reguly nie da sie zapisac w CHECK
--        (zalezy od historii w engagement_log), wiec zyje w kodzie: crm.dm_history()
--        + karta klasyfikacji bez rekomendacji. Tutaj tylko INDEKS, ktory ta kontrole
--        robi tania (jedno zapytanie per karta zamiast skanu tabeli).
--
-- Idempotentne: IF NOT EXISTS / ON CONFLICT. Mozna puscic drugi raz bez skutkow.

-- ---------- pkt 1 ----------
CREATE TABLE IF NOT EXISTS channel_kpi_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    brand_id        VARCHAR(50) NOT NULL,
    channel         VARCHAR(40) NOT NULL,
    metric_date     DATE NOT NULL,
    period          VARCHAR(10) NOT NULL DEFAULT 'dzien'
                    CHECK (period IN ('dzien', '7d', '28d', '90d')),
    impressions     INT,
    reactions       INT,
    new_followers   INT,
    followers_total INT,
    profile_views   INT,
    source          VARCHAR(30) NOT NULL DEFAULT 'raport_pracy'
                    CHECK (source IN ('raport_pracy', 'xlsx', 'api', 'reczny')),
    raw             JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (brand_id, channel, metric_date, period)
);

CREATE INDEX IF NOT EXISTS idx_kpi_snap_lookup
    ON channel_kpi_snapshots (brand_id, channel, metric_date DESC);

COMMENT ON TABLE  channel_kpi_snapshots IS
    'Metryki poziomu KANALU przepisane z panelu analitycznego (Lacznik, linia kpi_snapshot). Uzupelnienie channel_metrics_daily o okresy zbiorcze i o kanaly bez API.';
COMMENT ON COLUMN channel_kpi_snapshots.period IS
    'dzien (domyslnie) albo okres zbiorczy 7d/28d/90d; metric_date = KONIEC okresu';
COMMENT ON COLUMN channel_kpi_snapshots.raw IS
    'surowa linia raportu + pola nierozpoznane przez parser (zasada: nic nie ginie po cichu)';

-- Rejestr syncu: wiersz istnieje PO TO, zeby nocna kontrola driftu (03:00) widziala tabele.
-- enabled=FALSE zgodnie z planem iteracyjnego wlaczania (docs/cm/SYNC_ENABLE_PLAN.md):
-- wlaczamy dopiero po 24h czystej pracy, decyzja Tomasza.
INSERT INTO sync_registry (table_name, enabled, render_pattern, priority, config)
VALUES ('channel_kpi_snapshots', FALSE, 'append', 7, '{}'::jsonb)
ON CONFLICT (table_name) DO NOTHING;

-- ---------- pkt 5 ----------
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS who_is_who JSONB;

COMMENT ON COLUMN contacts.who_is_who IS
    'Kto jest kim po stronie klienta: {"role","influence_level","relationship_stage","source_of_data","notes"}. influence_level: decydent|wplywowy|uzytkownik|nieznany. source_of_data zawsze wypelnione - bez zrodla to plotka, nie dana.';

-- ---------- pkt 7 ----------
-- Fail-closed liczy historie DM z engagement_log (kolumny dm_history NIE MA i nie dodajemy jej:
-- historia zyje w logu, a duplikat w contacts natychmiast by sie rozjechal).
CREATE INDEX IF NOT EXISTS idx_eng_log_contact_action
    ON engagement_log (contact_id, action_type, created_at DESC);

-- ---------- kontrola ----------
SELECT 'channel_kpi_snapshots' AS co, COUNT(*)::text AS n FROM channel_kpi_snapshots
UNION ALL
SELECT 'sync_registry kpi', COUNT(*)::text FROM sync_registry WHERE table_name = 'channel_kpi_snapshots'
UNION ALL
SELECT 'contacts.who_is_who', COUNT(*)::text FROM information_schema.columns
    WHERE table_name = 'contacts' AND column_name = 'who_is_who'
UNION ALL
SELECT 'idx_eng_log_contact_action', COUNT(*)::text FROM pg_indexes
    WHERE indexname = 'idx_eng_log_contact_action';
