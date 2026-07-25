-- Wylaczenie auto-generowania grafik (25/07/2026, feedback Tomasza POWTORZONY).
--
-- Zgloszenie: "materialy graficzne generowane nie sa w sposob zadowalajacy - dopoki nie bedzie
-- dedykowanego agenta do tych spraw to chce to robic recznie - mam dostawac tylko szczegolowe
-- prompty." Kod juz zmieniony (zamiast obrazu dolacza szczegolowy prompt do karty), ten SQL to
-- druga warstwa: gasi flagi, ktore jeszcze moglyby wywolac generacje, i COFA P4 Managera
-- (auto_image X ON z 24/07 - decyzja wlasciciela o jego wlasnej marce wizualnej).
--
-- Wykonanie (SSH, Tomasz):
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/ops/grafiki_off_25072026.sql

\echo '--- 1) tor PRZED karta: cm_auto_image = false (bump wersji wzorcem brand_config) ---'
INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
VALUES ('AGS', 'cm_auto_image', 'false', 1, 'be-25072026', NOW())
ON CONFLICT (brand_id, config_key) DO UPDATE SET
  config_value = 'false', version = brand_config.version + 1,
  updated_by = 'be-25072026', updated_at = NOW();

\echo '--- 2) tor DISPATCH: channels.config.auto_image = false dla X i LinkedIn (cofniecie P4) ---'
UPDATE channels
   SET config = COALESCE(config, '{}'::jsonb) || '{"auto_image":"false"}'::jsonb
 WHERE brand_id = 'AGS' AND channel IN ('x', 'linkedin', 'linkedin_page');

\echo '--- 3) KONTROLA ---'
SELECT 'cm_auto_image' AS co, config_value AS wartosc
  FROM brand_config WHERE brand_id = 'AGS' AND config_key = 'cm_auto_image'
UNION ALL
SELECT 'auto_image ' || channel, config->>'auto_image'
  FROM channels WHERE brand_id = 'AGS' AND channel IN ('x', 'linkedin', 'linkedin_page')
 ORDER BY co;

-- Po wykonaniu: materialy "proszace sie o grafike" dostaja SZCZEGOLOWY PROMPT na karcie
-- (📋 SZCZEGOLOWY PROMPT + guzik 📋 Prompt), a zaden obraz nie generuje sie sam.
-- Zniesienie: dopiero dedykowany Agent Wizualny (backlog, wstrzymany przez Tomasza).
