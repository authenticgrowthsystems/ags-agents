-- CM Brain Faza 1 krok 1h (04/07/2026, ags_crd). Idempotent. Jezyk = DWA osobne ustawienia (R6, sprzedawalnosc):
-- language_comm (rozmowa bota, poziom marki) + channels.config.language_publish (per cel).

-- 1) jezyk komunikacji (rozmowa/menu/raporty): Tomasz = polski; klient zmienia przy onboardingu (/set language_comm en)
INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
VALUES ('AGS', 'language_comm', 'pl', 1, 'ddl-007', NOW())
ON CONFLICT (brand_id, config_key) DO NOTHING;

-- 2) jezyk publikacji per ISTNIEJACY cel (defaulty Tomasza 03/07: X AGS=EN, LinkedIn profil osobisty=EN)
UPDATE channels SET config = config || '{"language_publish": "en"}'::jsonb
WHERE brand_id='AGS' AND channel IN ('x', 'linkedin') AND NOT (config ? 'language_publish');

-- 3) przyszle cele (dojda z App 2 CMA - wiersze channels z jezykiem od razu w config):
--    LinkedIn strona AGS = en, LinkedIn TNM = pl, LinkedIn Royal Dance Center = pl
--    (INSERT przy aktywacji celu; wzor: config = '{"publish_mode":"draft","language_publish":"pl", ...}')
--    POPRAWIONE 19/08/2026 (D-020): wzor podawal 'webhook' - tryb ZABRONIONY od 22/07 po AP-307
--    (4-5 postow X w godzine, zgubione media, polski post na anglojezycznym profilu, baza klamiaca
--    o stanie). Wzor w komentarzu jest WYKONYWANY, nie oceniany (AP-316). Kod od 19/08 odmawia
--    ustawienia 'webhook': config.sprawdz_tryb_publikacji.
