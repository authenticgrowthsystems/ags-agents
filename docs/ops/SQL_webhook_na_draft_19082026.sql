-- =====================================================================================
-- D-020, czesc danych: dziewiec wierszy channels stoi w trybie 'webhook' (ZABRONIONY od
-- 22/07 po AP-307). Poprawka kodu z 19/08 zamyka produkcje NOWYCH takich wierszy;
-- istniejacych nie rusza. Decyzja Managera 19/08: prostujemy WSZYSTKIE na 'draft'.
--
-- Powod odrzucenia opcji "zostawic, bo aktywacja jest swiadoma": to warunek w glowie
-- czlowieka zamiast blokady, czyli dokladnie ta dziura, dla ktorej powstalo D-020 (AP-314).
--
-- URUCHAMIAC WYLACZNIE Z `ON_ERROR_STOP`:
--   docker exec -i pg_n8n psql -U n8n -d ags_crd -v ON_ERROR_STOP=1 < ten_plik.sql
--
-- RUNBOOK punkt 10: psql NIE podstawia zmiennych :nazwa wewnatrz bloku cytowanego dolarami,
-- wiec zadnych `:zmiennych` w `DO $$` tutaj nie ma. Liczby licza sie SAME, w transakcji.
-- RUNBOOK punkt 6: operacja pisze przez `jsonb_set`, a kontrola czyta przez operator
-- zawierania `@>`. INNY mechanizm, zeby ten sam blad nie oslepil obu.
-- =====================================================================================

BEGIN;

-- --- BRAMKA, ktora ma padac ZAMKNIETA (AP-314 punkt 2) -------------------------------
DO $$
DECLARE
    ile_webhook   integer;
    ile_aktywnych integer;
BEGIN
    SELECT count(*) INTO ile_webhook
      FROM channels WHERE config @> '{"publish_mode":"webhook"}'::jsonb;

    SELECT count(*) INTO ile_aktywnych
      FROM channels WHERE config @> '{"publish_mode":"webhook"}'::jsonb AND status = 'active';

    -- Porownanie z NULL przepuszcza po cichu, wiec NULL zatrzymuje jawnie.
    IF ile_webhook IS NULL OR ile_aktywnych IS NULL THEN
        RAISE EXCEPTION 'BRAMKA: licznik zwrocil NULL. Nie wiem, na czym pracuje. STOP.';
    END IF;

    IF ile_webhook = 0 THEN
        RAISE EXCEPTION 'BRAMKA: zero wierszy z trybem webhook. Albo ktos to juz zrobil, albo patrze na zla baze. STOP.';
    END IF;

    -- Decyzja Managera obejmowala DZIEWIEC wierszy, wszystkie w statusie ready. Kanal AKTYWNY
    -- z webhookiem to sytuacja NOWA i pilniejsza: strzela od razu, nie po aktywacji.
    -- Takiego przypadku ta decyzja NIE obejmuje - zatrzymaj sie i wroc do Managera.
    IF ile_aktywnych > 0 THEN
        RAISE EXCEPTION 'BRAMKA: % kanal(ow) AKTYWNYCH ma webhook. To nie jest przypadek objety decyzja z 19/08. STOP, wroc do Managera.', ile_aktywnych;
    END IF;

    RAISE NOTICE 'BRAMKA OK: % wierszy do poprawienia, zero aktywnych.', ile_webhook;
END $$;

-- --- STAN PRZED (do protokolu okna) --------------------------------------------------
SELECT brand_id, channel, status, config->>'publish_mode' AS tryb_przed
  FROM channels
 WHERE config @> '{"publish_mode":"webhook"}'::jsonb
 ORDER BY brand_id, channel;

-- --- OPERACJA ------------------------------------------------------------------------
-- jsonb_set podmienia WYLACZNIE klucz publish_mode. Reszta konfiguracji (language_publish,
-- secret_prefix, publish_windows, rules, slot_grid) zostaje nietknieta.
UPDATE channels
   SET config = jsonb_set(config, '{publish_mode}', '"draft"'::jsonb)
 WHERE config @> '{"publish_mode":"webhook"}'::jsonb;

-- --- KONTROLA PO, w tej samej transakcji ---------------------------------------------
DO $$
DECLARE
    zostalo integer;
BEGIN
    SELECT count(*) INTO zostalo
      FROM channels WHERE config @> '{"publish_mode":"webhook"}'::jsonb;

    IF zostalo IS NULL THEN
        RAISE EXCEPTION 'KONTROLA: licznik zwrocil NULL. STOP.';
    END IF;

    IF zostalo <> 0 THEN
        RAISE EXCEPTION 'KONTROLA: po zmianie zostalo % wierszy z webhook. Wycofuje.', zostalo;
    END IF;

    RAISE NOTICE 'KONTROLA OK: zero wierszy z trybem webhook.';
END $$;

COMMIT;

-- --- STAN PO (do protokolu okna) -----------------------------------------------------
SELECT brand_id, channel, status, config->>'publish_mode' AS tryb_po
  FROM channels
 ORDER BY brand_id, channel;

-- =====================================================================================
-- SQL ODWROTNY (RUNBOOK punkt 7) - ZAKOMENTOWANY CELOWO.
-- Przywraca 'webhook' DOKLADNIE tym dziewieciu wierszom. Odkomentuj i uruchom TYLKO
-- wtedy, gdy Manager cofnie decyzje z 19/08. Pamietaj, ze tryb jest zabroniony i kod
-- od 19/08 odmawia jego USTAWIENIA - to odwrocenie omija bramke, bo pisze wprost do bazy.
--
-- BEGIN;
-- UPDATE channels SET config = jsonb_set(config, '{publish_mode}', '"webhook"'::jsonb)
--  WHERE (brand_id, channel) IN (
--    ('AGS','facebook'), ('AGS','instagram'), ('AGS','youtube'), ('AGS','linkedin_page'),
--    ('LYSY','linkedin'), ('PT','linkedin'), ('RDC','linkedin'), ('SDI','linkedin'),
--    ('TNM','linkedin'));
-- COMMIT;
-- =====================================================================================
