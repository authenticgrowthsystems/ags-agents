-- DDL 042 (03/08/2026): D-008 - nowa wartosc `content_items.status = 'handed_off'`
-- DOPISANA OBOK starej, nie zamiast niej.
--
-- KONTEKST: `dispatching` brzmialo jak stan PRZELOTNY ("wysylam"), a znaczy "rozeslane do kolejki,
-- czekam az wszystkie wiersze serii osiagna stan terminalny" - czyli stan, ktory trwa DNI.
-- 27/07 Manager zglosil zawieszony post; odczyt pokazal siedem materialow, WSZYSTKIE ZDROWE,
-- najstarszy 51 godzin i poprawnie, bo jego sloty siegaly 4 sierpnia. To AP-312.
--
-- DLACZEGO 'handed_off', a nie 'awaiting_publication' (decyzja Tomasza 03/08):
-- stan konczy sie, gdy wiersze kolejki przestaja sie ruszac - OBOJETNIE CZYM. `_DISPATCH_OK`
-- zawiera 'held' (gotowiec do recznej wklejki), wiec przy LinkedInie material wychodzi ze stanu,
-- a publikacja dopiero czeka na czlowieka. Nazwa obiecujaca publikacje odtworzylaby AP-312
-- wewnatrz poprawki na AP-312. Osobno: `agent_registry.current_gate` uzywa juz przedrostka
-- awaiting_* w ZNACZENIU "czekam na bramke zatwierdzenia".
--
-- UWAGA, NAJWAZNIEJSZE ZDANIE W TYM PLIKU:
--   `post_queue.status` MA WLASNA wartosc 'dispatching' i to jest INNY SLOWNIK (jeden wiersz
--   kolejki oddany subagentowi). D-008 jej NIE DOTYKA. Nie rob podmiany "po calej bazie".
--
-- DLACZEGO OBOK, A NIE ZAMIAST: migracja danych musi miec chwile, w ktorej obie wartosci sa
-- dozwolone - inaczej UPDATE nie ma jak przebiec. Stara wartosc znika z ograniczenia dopiero
-- w OSOBNYM oknie, innego dnia (decyzja Tomasza 03/08):
--   docs/ops/SQL_d008b_sprzatanie_check_PO_OKNIE.sql
--
-- Uruchomienie (PRZED migracja danych, przy zatrzymanych pisarzach):
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/042_status_handed_off.sql
-- Idempotentne.

\encoding UTF8
\set ON_ERROR_STOP on

-- Limit czasu blokady: ALTER TABLE bierze ACCESS EXCLUSIVE. Jesli cos trzyma tabele, wolimy
-- czysty blad po 5 sekundach niz kolejke zablokowanych zapytan.
SET lock_timeout = '5s';

ALTER TABLE content_items DROP CONSTRAINT IF EXISTS content_items_status_check;
ALTER TABLE content_items ADD CONSTRAINT content_items_status_check
  CHECK (status IN ('proposed','planned','needs_research','researching','drafting','needs_approval',
                    'approved','handed_off','dispatching','published','rejected','failed',
                    'draft','brief','archived'));

COMMENT ON COLUMN content_items.status IS
  'Stan MATERIALU. handed_off = rozeslany do kolejki, czeka az WSZYSTKIE wiersze post_queue tej serii przestana sie ruszac (published ALBO held ALBO failed) - stan normalnie trwa DNI, nie sekundy. Do 03/08/2026 nazywal sie dispatching (D-008/AP-312: nazwa obiecywala stan przelotny). UWAGA: post_queue.status ma WLASNA wartosc dispatching i znaczy ona co innego - jeden wiersz kolejki oddany subagentowi.';

\echo '--- KONTROLA: ograniczenie zna obie wartosci (przejsciowo) ---'
SELECT pg_get_constraintdef(oid) AS ograniczenie
  FROM pg_constraint WHERE conname = 'content_items_status_check';

\echo '--- KONTROLA: rozklad statusow PRZED migracja danych ---'
SELECT status, COUNT(*) AS n FROM content_items GROUP BY status ORDER BY 2 DESC;
