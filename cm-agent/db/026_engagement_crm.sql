-- =============================================================================
-- 026_engagement_crm.sql (BE-ENGAGEMENT 20/07/2026)
-- Brief: docs/briefs/BRIEF_ENGAGEMENT_CRM_20072026.md
-- CRM relacji dla comment-radaru: propozycja per autor = wiersz engagement_log
-- z contact_id, stadium relacji na kontakcie, handles multi-platforma,
-- cykl zycia propozycji (status) zamiast decyzji doklejanych do notes.
-- Idempotentne (IF NOT EXISTS / DROP+ADD constraint). AP-304: stan zastany
-- zweryfikowany w repo (001_initial_schema + audyt DB 04/07): contacts MA juz
-- handles jsonb (wg audytu) i zdublowane kolumny (konsolidacja POZA zakresem);
-- engagement_log.contact_id FK istnieje od 001. Ponizsze ALTERy sa pasem
-- bezpieczenstwa - na zywej bazie wykonaja sie jako no-op tam, gdzie kolumna jest.
-- Wykonanie (SSH):
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/026_engagement_crm.sql
-- =============================================================================

-- 1) contacts: jedna osoba, wiele kont - handles jsonb {"x": "handle", "linkedin": "slug"}
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS handles jsonb NOT NULL DEFAULT '{}'::jsonb;

-- 2) contacts: stadium relacji. Skala ZATWIERDZONA przez Tomasza guzikami 20/07:
--    cold -> commented -> replied -> dm -> offer -> client (liniowo, bump tylko w przod)
--    + 'ghosted' jako stan boczny (relacja ucichla; ustawiany recznie/przyszlymi akcjami,
--    poza liniowym awansem).
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS relationship_stage varchar(20) NOT NULL DEFAULT 'cold';
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'contacts_relationship_stage_check') THEN
    ALTER TABLE contacts ADD CONSTRAINT contacts_relationship_stage_check
      CHECK (relationship_stage IN ('cold','commented','replied','dm','offer','client','ghosted'));
  END IF;
END $$;

-- 3) contacts.icp_tier: doktryna ICP #71 (Buyer/Peer/Competitor/Partner) DOCHODZI do wartosci
--    legacy z 001 (Premium/Mid/Free/Watch/N/A - 45 zywych wierszy). Konsolidacja obu skal
--    = znany dlug "konsolidacja contacts przed agentem CRM" (audyt 04/07 pkt 3), poza zakresem.
ALTER TABLE contacts DROP CONSTRAINT IF EXISTS contacts_icp_tier_check;
ALTER TABLE contacts ADD CONSTRAINT contacts_icp_tier_check
  CHECK (icp_tier IS NULL OR icp_tier IN
         ('Buyer','Peer','Competitor','Partner','Premium','Mid','Free','Watch','N/A'));

-- 4) engagement_log.contact_id: FK istnieje od 001_initial_schema - pas bezpieczenstwa
ALTER TABLE engagement_log ADD COLUMN IF NOT EXISTS contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_engagement_contact_id ON engagement_log(contact_id);

-- 5) engagement_log: cykl zycia propozycji komentarza (koniec decyzji rozpoznawanych z prozy w notes)
--    logged   = wpis historyczny / nie-propozycja (default dla starych wierszy)
--    proposed = propozycja czeka na decyzje Tomasza (guziki cmt:)
--    approved = zatwierdzona, gotowiec w task_queue
--    rejected = odrzucona (takze: zastapiona innym katem / analiza wielozrzutowa)
--    sent     = Tomasz potwierdzil wklejenie komentarza
--    skipped  = pominieta swiadomie
ALTER TABLE engagement_log ADD COLUMN IF NOT EXISTS status varchar(20) NOT NULL DEFAULT 'logged';
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'engagement_log_status_check') THEN
    ALTER TABLE engagement_log ADD CONSTRAINT engagement_log_status_check
      CHECK (status IN ('logged','proposed','approved','rejected','sent','skipped'));
  END IF;
END $$;

-- 6) engagement_log: autor propozycji jawnie (dotad ginal w notes 'od: X')
ALTER TABLE engagement_log ADD COLUMN IF NOT EXISTS author_display varchar(200);

CREATE INDEX IF NOT EXISTS idx_engagement_status_open ON engagement_log(status)
  WHERE status IN ('proposed','approved');

-- Weryfikacja (recznie):
-- SELECT column_name FROM information_schema.columns WHERE table_name='contacts'
--   AND column_name IN ('handles','relationship_stage');
-- SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
--   WHERE conname IN ('contacts_icp_tier_check','contacts_relationship_stage_check','engagement_log_status_check');
-- SELECT column_name FROM information_schema.columns WHERE table_name='engagement_log'
--   AND column_name IN ('contact_id','status','author_display');
