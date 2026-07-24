-- 028 (24/07/2026): nowy typ materialu sprzedazowego 'outreach_example'.
--
-- Po co: wiadomosci, ktore Tomasz NAPRAWDE wyslal, ida do promptu gotowca DOSLOWNIE jako wzorzec
-- rytmu i sposobu wejscia w temat (_outreach_examples w cm-agent/app/sales.py). Model pisze wtedy
-- od jego zdan, nie od teorii. Bez tego typu wzorce mieszalyby sie z ksiazkami i technikami
-- w wyszukiwaniu semantycznym.
--
-- AP-304 (recydywa 24/07): kod dopisal nowy typ, a tabela ma CHECK z siedmioma wartosciami -
-- INSERT lecial bledem 'violates check constraint'. Kolumny i ograniczenia sprawdzamy PRZED
-- generowaniem SQL, nie po.
--
-- Idempotentne: DROP IF EXISTS + ADD.

ALTER TABLE sales_knowledge DROP CONSTRAINT IF EXISTS sales_knowledge_material_type_check;

ALTER TABLE sales_knowledge ADD CONSTRAINT sales_knowledge_material_type_check
    CHECK (material_type IN ('book', 'technique', 'case_study', 'framework', 'script',
                             'recording', 'outreach_example', 'other'));
