-- AKTYWACJA PAKIETOW PL (DFY System Retencji) - 20/07/2026, BE-PRODUKT
-- WYKONUJE TOMASZ przez SSH PO decyzji guzikami (aktywacja + ostateczne kwoty).
-- NIE wykonywac przed decyzja. Build BE-PRODUKT = zero DDL/deployu (ten plik to gotowiec).
--
-- Krok 1 (zawsze przy TAK): parking_active -> active dla 3 Pakietow PL.
UPDATE pricing_tiers
   SET meta_status = 'active'
 WHERE brand_id = 'AGS'
   AND ladder = 'lokalna_automatyzacja'
   AND meta_status = 'parking_active';

-- Krok 2 (TYLKO jesli Tomasz zatwierdzi propozycje EN z oferty; kwoty moga sie zmienic
-- decyzja guzikami - wtedy podmien wartosci price przed wykonaniem):
INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, meta_status)
VALUES
  ('AGS', 'retention_en', 'Foundation', '700-1000 USD one-time', 'USD',
   '{"maps_to": "Pakiet 1: Strona WWW", "delivery_days": "5-7", "tool_sub": "$97-297/mo paid by client"}'::jsonb,
   'active'),
  ('AGS', 'retention_en', 'Website + Core Automation', '1200-1900 USD one-time', 'USD',
   '{"maps_to": "Pakiet 2: Strona + Podstawowa Automatyzacja", "delivery_days": "7-10", "tool_sub": "$97-297/mo paid by client"}'::jsonb,
   'active'),
  ('AGS', 'retention_en', 'Complete Retention System', '2500-3500 USD one-time', 'USD',
   '{"maps_to": "Pakiet 3: Kompletny System", "delivery_days": "10-14", "tool_sub": "$97-297/mo paid by client"}'::jsonb,
   'active')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

-- Weryfikacja (wynik wklej do czatu):
SELECT ladder, tier_name, price, currency, meta_status
  FROM pricing_tiers
 WHERE ladder IN ('lokalna_automatyzacja', 'retention_en')
 ORDER BY ladder, tier_name;
-- Oczekiwane: 3x lokalna_automatyzacja meta_status=active (+ ew. 3x retention_en active).

-- Komenda (SSH Mikrus, po wgraniu pliku przez git pull):
-- docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/product/SQL_AKTYWACJA_PAKIETOW_PL_20072026.sql
