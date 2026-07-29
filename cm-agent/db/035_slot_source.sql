-- DDL 035 (29/07/2026): slad audytowy zrodla slotu w kolejce publikacji.
--
-- POWOD (decyzja Managera 29/07, rekomendacja BE): 28 lipca piec wpisow wyszlo na X w piec
-- minut, o 09:00, poza oknem publikacji 13:00-22:00, na koncie ktore trzy dni wczesniej
-- dostalo 403 za wykryta automatyzacje. Ustalenie, KTO nadal ten slot, zajelo pol godziny
-- i udalo sie WYLACZNIE przez eliminacje wszystkich innych drog zapisu:
--   * slots.assign_if_needed odpada, bo celowo daje kolejce czas uludzki (ci i pq MUSZA sie
--     roznic, a tam byly identyczne co do sekundy),
--   * reslot odpada, bo nadaje minute 3-13 i jest skryptem recznym poza petla,
--   * wezly n8n odpadaja, bo celuja w pojedynczy wiersz, nie ruszaja content_items,
--     a ich godziny pochodza z tablicy 14/18/22.
-- Zostala jedna trasa: reczne przesuniecie terminu materialu przez rozmowe
-- (conversation.py:1286-1290). W danych nie bylo ANI JEDNEGO sladu, ktory by to powiedzial.
--
-- To jest AP-311 w wersji zapobiegawczej: brak danych nie jest faktem o swiecie, dopoki nie
-- sprawdzisz, czy system mial jak je pokazac. Tutaj po prostu nie mial.
--
-- ZAKRES CELOWO MALY (polecenie Managera: "jedna kolumna, bez nazwisk i bez historii"):
-- sama etykieta zrodla, nic wiecej. Kto konkretnie i o ktorej - poza zakresem.
--
-- Wartosc 'nieznane' jest DOMYSLNA i znaczaca: tak oznaczy sie kazdy zapis spoza Pythona
-- (wezly n8n, reczny SQL). Nie udajemy, ze wiemy, skad przyszedl - mowimy, ze nie wiemy.
--
-- Idempotentne: ADD COLUMN IF NOT EXISTS.

ALTER TABLE post_queue ADD COLUMN IF NOT EXISTS slot_source TEXT NOT NULL DEFAULT 'nieznane';

COMMENT ON COLUMN post_queue.slot_source IS
    'Kto ostatnio ustawil scheduled_for: staging (channels.stage_variant), planner (slots.assign_if_needed), reslot (app.reslot), rozmowa (przesuniecie terminu przez czlowieka), dispatch (channels przy wypuszczeniu), nieznane (zapis spoza Pythona: n8n albo reczny SQL). Sluzy do odpowiedzi na pytanie "skad ten slot" bez eliminowania tras po kolei.';

-- Odczyt diagnostyczny bedzie zawsze ten sam: grupuj po zrodle i szukaj salw.
CREATE INDEX IF NOT EXISTS idx_post_queue_slot_source
    ON post_queue (slot_source, scheduled_for);

-- ---------- kontrola ----------
SELECT 'kolumna slot_source' AS co,
       (SELECT COUNT(*)::text FROM information_schema.columns
         WHERE table_name='post_queue' AND column_name='slot_source') AS n
UNION ALL
SELECT 'indeks',
       (SELECT COUNT(*)::text FROM pg_indexes WHERE indexname='idx_post_queue_slot_source')
UNION ALL
SELECT 'rozklad zrodel (wszystko historyczne = nieznane)',
       COALESCE(string_agg(slot_source || '=' || n::text, ', ' ORDER BY slot_source), '(pusto)')
  FROM (SELECT slot_source, COUNT(*) AS n FROM post_queue GROUP BY slot_source) s;
