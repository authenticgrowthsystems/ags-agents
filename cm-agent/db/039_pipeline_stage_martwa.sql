-- DDL 039 (02/08/2026): D-010 - `contacts.pipeline_stage` oznaczona jako MARTWA.
--
-- USTALENIE Z ODCZYTU: `contacts` ma TRZY kolumny opisujace stan tej samej osoby.
--   * `relationship_stage` varchar(20) NOT NULL, CHECK na 7 wartosci - ZYWA, wypelniona zawsze
--     (cold 121, commented 69, dm 4). To jest zrodlo prawdy o stadium relacji.
--   * `status` varchar(50) NOT NULL, CHECK na 7 INNYCH wartosci (Cold/Warm/Hot/Customer/...) -
--     ZYWA, opisuje temperature, nie relacje. Wspolistnienie tych dwoch da sie obronic.
--   * `pipeline_stage` **text, BEZ ograniczenia, wypelniona w 45 wierszach** - i CZYTA JA NIKT.
--     Grep po calym `cm-agent/app/` (02/08): ZERO trafien poza definicja schematu.
--
-- DLACZEGO NIE USUWAM KOLUMNY: usuniecie jest nieodwracalne i zabiera 45 wartosci, ktorych
-- pochodzenia dzis nie znamy. Kolumna nikomu nie szkodzi dopoki nikt jej nie czyta - a szkodzic
-- zacznie w chwili, gdy KTOS ja przeczyta, biorac za zrodlo prawdy o etapie.
--
-- DLATEGO KOMENTARZ, A NIE DROP: to jest lekarstwo na AP-312 (nazwa obiecuje cos innego, niz
-- znaczy) podane tam, gdzie nastepny agent NAPRAWDE zajrzy - w schemacie bazy, nie w pliku
-- dokumentacji, ktorego moze nie otworzyc. `pipeline_stage` brzmi jak etap w lejku sprzedazy
-- i wlasnie dlatego jest grozna: to zaproszenie do pomylki, nie zwykly balast.
--
-- Uruchomienie: psql -U n8n -d ags_crd -f 039_pipeline_stage_martwa.sql  (idempotentne, bez zapisu danych)

COMMENT ON COLUMN contacts.pipeline_stage IS
  'MARTWA OD 02/08/2026 (dlug D-010). NIE CZYTAJ i NIE PISZ. Nazwa sugeruje etap w lejku sprzedazy, ale lejek zyje w sales_pipeline.stage, a stadium relacji kontaktu w contacts.relationship_stage. Ta kolumna nie ma ograniczenia CHECK, nikt jej nie czyta (grep 02/08: zero trafien w kodzie) i pozostale 45 wypelnionych wartosci ma nieznane pochodzenie. Zostawiona zamiast usuniecia, bo DROP jest nieodwracalny.';

COMMENT ON COLUMN contacts.relationship_stage IS
  'ZRODLO PRAWDY o stadium relacji z kontaktem: cold / commented / replied / dm / offer / client / ghosted. To po tym pyta kod, nie po pipeline_stage.';

COMMENT ON COLUMN contacts.status IS
  'TEMPERATURA kontaktu (Cold/Warm/Hot/Customer/Ghosted/Peer/Competitor) - inna os niz relationship_stage i celowo osobna. Nie mylic z etapem lejka (sales_pipeline.stage).';

-- WERYFIKACJA (odczyt):
-- SELECT column_name, col_description('contacts'::regclass, ordinal_position) AS opis
--   FROM information_schema.columns
--  WHERE table_name='contacts' AND column_name IN ('pipeline_stage','relationship_stage','status');
