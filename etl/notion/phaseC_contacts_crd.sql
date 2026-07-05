-- TASK #71 FAZA C (K5): contacts <- CRD Top15 + watchlist + INFLUENCER LIST v2.0 (05/07/2026).
-- Dedup po full_name (zasada DB-first: zero duplikacji osob); AP-303 dollar-quote; idempotentne.
-- UWAGA do raportu: kontrakt mowil '32 konta' (v1.0); LIVE strona = v2.0 z 21 kontami (walidacja 18/04).

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Erica Wood$c$, $c$Erica Wood$c$, $c$Ghosted$c$, $c$Premium $2K+$c$, $c$P1$c$, $c$door_open$c$, $c$Outbound DM$c$, $c$Soft no 30/05, relationship preserved, door open.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#erica-wood$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Erica Wood$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Pawel M. Pawlak PhD$c$, $c$Pawel M. Pawlak PhD$c$, $c$Warm$c$, $c$Premium $2K+$c$, $c$P0$c$, $c$ready_for_dm$c$, $c$Outbound DM$c$, $c$HIGH PRIORITY sciezka M5. Ready for DM per CM 25-29/05.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#pawel-pawlak$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Pawel M. Pawlak PhD$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Danielle Tworek$c$, $c$Danielle Tworek$c$, $c$Warm$c$, $c$Premium $2K+$c$, $c$P1$c$, $c$warm$c$, $c$Mention$c$, $c$Wymienila Tomasza publicznie.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#danielle-tworek$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Danielle Tworek$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Will McTighe$c$, $c$Will McTighe$c$, $c$Warm$c$, $c$Premium $2K+$c$, $c$P1$c$, $c$building$c$, $c$Comment$c$, $c$Building relacji, 5 odpowiedzi w watku.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#will-mctighe$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Will McTighe$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Safwan Umair$c$, $c$Safwan Umair$c$, $c$Warm$c$, $c$Mid $97-297$c$, $c$P2$c$, $c$warm$c$, $c$Comment$c$, $c$Warm signal: skomentowal post.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#safwan-umair$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Safwan Umair$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Lacy Boggs$c$, $c$Lacy Boggs$c$, $c$Warm$c$, $c$Watch (peer/competitor)$c$, $c$P2$c$, $c$verify_intent$c$, $c$Inbound DM$c$, $c$INBOUND ale #OPENTOWORK - weryfikacja intencji pending.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#lacy-boggs$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Lacy Boggs$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Matthew Case$c$, $c$Matthew Case$c$, $c$Cold$c$, $c$Premium $2K+$c$, $c$P3$c$, $c$hold_stage2$c$, $c$Outbound DM$c$, $c$Hold do Stage 2.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#matthew-case$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Matthew Case$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Stephen Conley$c$, $c$Stephen Conley$c$, $c$Cold$c$, $c$Premium $2K+$c$, $c$P3$c$, $c$hold_stage1$c$, $c$Outbound DM$c$, $c$Hold do Stage 1.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#stephen-conley$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Stephen Conley$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Tracye Warfield$c$, $c$Tracye Warfield$c$, $c$Ghosted$c$, $c$Premium $2K+$c$, $c$P3$c$, $c$hold$c$, $c$Outbound DM$c$, $c$Cold/Ghost, hold do 02/06. HOT Stage 3 wg listy influencerow (zacytowala fraze Tomasza 'Space isn't created. It's chosen.').$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#tracye-warfield$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Tracye Warfield$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Maryse Vaillant$c$, $c$Maryse Vaillant$c$, $c$Cold$c$, $c$Watch (peer/competitor)$c$, $c$P3$c$, $c$watch$c$, $c$Comment$c$, $c$Potencjalny - obserwacja.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#maryse-vaillant$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Maryse Vaillant$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Sukhdeep Singh$c$, $c$Sukhdeep Singh$c$, $c$Peer$c$, $c$Watch (peer/competitor)$c$, $c$P1$c$, $c$peer_relationship$c$, $c$Comment$c$, $c$Podarowal frame 'sovereign architect' (Hormozi thread). Warm DM T+24-48h. Credit obowiazkowy przy uzyciu frame.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#sukhdeep-singh$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Sukhdeep Singh$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Ashley Morris$c$, $c$Ashley Morris$c$, $c$Peer$c$, $c$Watch (peer/competitor)$c$, $c$P2$c$, $c$peer_relationship$c$, $c$Comment$c$, $c$Co-founder inNotion, skomentowala post TNM.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#ashley-morris$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Ashley Morris$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Dr. Suzanne Morgan$c$, $c$Dr. Suzanne Morgan$c$, $c$Peer$c$, $c$Watch (peer/competitor)$c$, $c$P2$c$, $c$first_follower$c$, $c$Mention$c$, $c$Pierwsza followerka TNM (reakcja 29/05).$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#suzanne-morgan$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Dr. Suzanne Morgan$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Charlie Hills$c$, $c$Charlie Hills$c$, $c$Peer$c$, $c$Watch (peer/competitor)$c$, $c$P2$c$, $c$watch$c$, $c$Mention$c$, $c$Material na viral case study. AI tools curator (Claude/MCP), 1900+ reactions - tech-savvy founder audience.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#charlie-hills$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Charlie Hills$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, priority, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Suzanne Taylor-King (STK)$c$, $c$Suzanne Taylor-King (STK)$c$, $c$Competitor$c$, $c$Watch (peer/competitor)$c$, $c$P3$c$, $c$closed_competitor$c$, $c$Inbound DM$c$, $c$Zamknieta per ICP Doctrine: profil 'founder teaching AI OS' = Peer->Competitor-adjacent. MOOT.$c$, 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#suzanne-taylor-king$c$, ARRAY['crd_top15']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Suzanne Taylor-King (STK)$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, brand_affinity, notion_page_id, tags)
SELECT $c$Pieter Levels$c$, $c$Pieter Levels$c$, 'Peer', 'Watch (peer/competitor)', 'watchlist', 'Watchlist', 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#watch-pieter-levels$c$, ARRAY['crd_watchlist_sample']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Pieter Levels$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, brand_affinity, notion_page_id, tags)
SELECT $c$Daniel Paul$c$, $c$Daniel Paul$c$, 'Peer', 'Watch (peer/competitor)', 'watchlist', 'Watchlist', 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#watch-daniel-paul$c$, ARRAY['crd_watchlist_sample']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Daniel Paul$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, brand_affinity, notion_page_id, tags)
SELECT $c$Nabeel Ahmed$c$, $c$Nabeel Ahmed$c$, 'Peer', 'Watch (peer/competitor)', 'watchlist', 'Watchlist', 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#watch-nabeel-ahmed$c$, ARRAY['crd_watchlist_sample']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Nabeel Ahmed$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, brand_affinity, notion_page_id, tags)
SELECT $c$Jessie van Breugel$c$, $c$Jessie van Breugel$c$, 'Peer', 'Watch (peer/competitor)', 'watchlist', 'Watchlist', 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#watch-jessie-van-breugel$c$, ARRAY['crd_watchlist_sample']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Jessie van Breugel$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, brand_affinity, notion_page_id, tags)
SELECT $c$Celeste Yamile$c$, $c$Celeste Yamile$c$, 'Peer', 'Watch (peer/competitor)', 'watchlist', 'Watchlist', 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#watch-celeste-yamile$c$, ARRAY['crd_watchlist_sample']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Celeste Yamile$c$);

INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, brand_affinity, notion_page_id, tags)
SELECT $c$Fraol Mussa$c$, $c$Fraol Mussa$c$, 'Peer', 'Watch (peer/competitor)', 'watchlist', 'Watchlist', 'AGS', $c$371c00c90b9381ec9b13c1d910c9a547#watch-fraol-mussa$c$, ARRAY['crd_watchlist_sample']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Fraol Mussa$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 1] Young and Profiting Podcast, CEO (100K+, Follow-only). Odpowiedziala personalnie, polubila komentarz. Audience founderow.$c$
WHERE full_name = $c$Hala Taha$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Hala Taha$c$, $c$Hala Taha$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 1] Young and Profiting Podcast, CEO (100K+, Follow-only). Odpowiedziala personalnie, polubila komentarz. Audience founderow.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t1-hala-taha$c$, ARRAY['influencer_v2','tier1']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Hala Taha$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 1] Speaker, Author, Coach (1st conn., Connect). HOT Stage 3. Zacytowala fraze Tomasza.$c$
WHERE full_name = $c$Tracye Warfield$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Tracye Warfield$c$, $c$Tracye Warfield$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 1] Speaker, Author, Coach (1st conn., Connect). HOT Stage 3. Zacytowala fraze Tomasza.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t1-tracye-warfield$c$, ARRAY['influencer_v2','tier1']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Tracye Warfield$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 1] AI tools, trends & adoption (1st conn., Connect). 5 wymian merytorycznych, wymienil Tomasza trzykrotnie.$c$
WHERE full_name = $c$Kushal Sthapak$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Kushal Sthapak$c$, $c$Kushal Sthapak$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 1] AI tools, trends & adoption (1st conn., Connect). 5 wymian merytorycznych, wymienil Tomasza trzykrotnie.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t1-kushal-sthapak$c$, ARRAY['influencer_v2','tier1']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Kushal Sthapak$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 1] LinkedIn Algorithm Researcher (100K+, Follow-only). Algorithm Report 2026. 2 komentarze zwalidowane.$c$
WHERE full_name = $c$Richard van der Blom$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Richard van der Blom$c$, $c$Richard van der Blom$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 1] LinkedIn Algorithm Researcher (100K+, Follow-only). Algorithm Report 2026. 2 komentarze zwalidowane.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t1-richard-van-der-blom$c$, ARRAY['influencer_v2','tier1']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Richard van der Blom$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 1] Buy Back Your Time (177K, Follow-only). Komentarz hybrydowy taniec+system. Founderzy.$c$
WHERE full_name = $c$Dan Martell$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Dan Martell$c$, $c$Dan Martell$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 1] Buy Back Your Time (177K, Follow-only). Komentarz hybrydowy taniec+system. Founderzy.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t1-dan-martell$c$, ARRAY['influencer_v2','tier1']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Dan Martell$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 1] Solopreneur educator (1M+, Follow-only). Komentarz 'passion vs freedom' walidowany.$c$
WHERE full_name = $c$Justin Welsh$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Justin Welsh$c$, $c$Justin Welsh$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 1] Solopreneur educator (1M+, Follow-only). Komentarz 'passion vs freedom' walidowany.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t1-justin-welsh$c$, ARRAY['influencer_v2','tier1']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Justin Welsh$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 1] Customer psychology, The Why Axis (80K+, Follow-only). Komentarz spojny z historia Tomasza.$c$
WHERE full_name = $c$Katelyn Bourgoin$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Katelyn Bourgoin$c$, $c$Katelyn Bourgoin$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 1] Customer psychology, The Why Axis (80K+, Follow-only). Komentarz spojny z historia Tomasza.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t1-katelyn-bourgoin$c$, ARRAY['influencer_v2','tier1']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Katelyn Bourgoin$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 1] Revenue Recovery, solopreneurs (1st conn., Connect). HOT Stage 2. Aktywna wymiana.$c$
WHERE full_name = $c$Shannon Vital$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Shannon Vital$c$, $c$Shannon Vital$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 1] Revenue Recovery, solopreneurs (1st conn., Connect). HOT Stage 2. Aktywna wymiana.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t1-shannon-vital$c$, ARRAY['influencer_v2','tier1']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Shannon Vital$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 2] Acquisition.com, $100M Offers (1M+, Follow-only). Komentarz 'difficulty without direction' = 6 reakcji.$c$
WHERE full_name = $c$Alex Hormozi$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Alex Hormozi$c$, $c$Alex Hormozi$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 2] Acquisition.com, $100M Offers (1M+, Follow-only). Komentarz 'difficulty without direction' = 6 reakcji.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t2-alex-hormozi$c$, ARRAY['influencer_v2','tier2']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Alex Hormozi$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 2] HubSpot co-founder, AI (mega, Follow-only). AI + entrepreneurship, czyste AGS ICP.$c$
WHERE full_name = $c$Dharmesh Shah$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Dharmesh Shah$c$, $c$Dharmesh Shah$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 2] HubSpot co-founder, AI (mega, Follow-only). AI + entrepreneurship, czyste AGS ICP.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t2-dharmesh-shah$c$, ARRAY['influencer_v2','tier2']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Dharmesh Shah$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 2] CEO Polished Carbon (694K, Follow-only). Leadership, CEO/founders ICP. Viral posts.$c$
WHERE full_name = $c$Justin Wright$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Justin Wright$c$, $c$Justin Wright$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 2] CEO Polished Carbon (694K, Follow-only). Leadership, CEO/founders ICP. Viral posts.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t2-justin-wright$c$, ARRAY['influencer_v2','tier2']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Justin Wright$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 2] Key Person of Influence (wysoki, Connect/Follow). Authority-builders = klienci AGS.$c$
WHERE full_name = $c$Daniel Priestley$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Daniel Priestley$c$, $c$Daniel Priestley$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 2] Key Person of Influence (wysoki, Connect/Follow). Authority-builders = klienci AGS.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t2-daniel-priestley$c$, ARRAY['influencer_v2','tier2']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Daniel Priestley$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 2] Personal branding for founders (1M+, 1st conn.). Familiarity-first walidacja, Connect po 3 tyg. komentowania.$c$
WHERE full_name = $c$Lara Acosta$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Lara Acosta$c$, $c$Lara Acosta$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 2] Personal branding for founders (1M+, 1st conn.). Familiarity-first walidacja, Connect po 3 tyg. komentowania.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t2-lara-acosta$c$, ARRAY['influencer_v2','tier2']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Lara Acosta$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 2] Frameworks for founders (1M+, Follow-only). Founderzy scrolluja jego feed.$c$
WHERE full_name = $c$Sahil Bloom$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Sahil Bloom$c$, $c$Sahil Bloom$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 2] Frameworks for founders (1M+, Follow-only). Founderzy scrolluja jego feed.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t2-sahil-bloom$c$, ARRAY['influencer_v2','tier2']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Sahil Bloom$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 2] Contrarian Thinking (wysoki, Follow-only). Operators i systemy, founders z kapitalem.$c$
WHERE full_name = $c$Codie Sanchez$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Codie Sanchez$c$, $c$Codie Sanchez$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 2] Contrarian Thinking (wysoki, Follow-only). Operators i systemy, founders z kapitalem.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t2-codie-sanchez$c$, ARRAY['influencer_v2','tier2']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Codie Sanchez$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 3] Google AI Transformation Leader (wysoki, Follow-only). Komentarz Agentic AI = 4 reakcje + polecenie.$c$
WHERE full_name = $c$Amit Rawal$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Amit Rawal$c$, $c$Amit Rawal$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 3] Google AI Transformation Leader (wysoki, Follow-only). Komentarz Agentic AI = 4 reakcje + polecenie.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t3-amit-rawal$c$, ARRAY['influencer_v2','tier3']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Amit Rawal$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 3] LinkedIn & X content dla CEOs (1st conn., Connect). Komentarz 'authorship gap' - reply 'exactly this'. Peer.$c$
WHERE full_name = $c$Konstantinos Karakostas$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Konstantinos Karakostas$c$, $c$Konstantinos Karakostas$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 3] LinkedIn & X content dla CEOs (1st conn., Connect). Komentarz 'authorship gap' - reply 'exactly this'. Peer.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t3-konstantinos-karakostas$c$, ARRAY['influencer_v2','tier3']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Konstantinos Karakostas$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 3] AI Biznes Lab, ex-Microsoft (31K, 1st conn.). PL lane, Partner candidate, zaakceptowal Connect.$c$
WHERE full_name = $c$Mirek Burnejko$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Mirek Burnejko$c$, $c$Mirek Burnejko$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 3] AI Biznes Lab, ex-Microsoft (31K, 1st conn.). PL lane, Partner candidate, zaakceptowal Connect.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t3-mirek-burnejko$c$, ARRAY['influencer_v2','tier3']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Mirek Burnejko$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 3] AI tools curator, Claude/MCP (wysoki, Follow/Connect). 1900+ reactions. Tech-savvy founder audience.$c$
WHERE full_name = $c$Charlie Hills$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Charlie Hills$c$, $c$Charlie Hills$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 3] AI tools curator, Claude/MCP (wysoki, Follow/Connect). 1900+ reactions. Tech-savvy founder audience.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t3-charlie-hills$c$, ARRAY['influencer_v2','tier3']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Charlie Hills$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 3] Scale Without Increasing Headcount (48K, Connect/Follow). Operators scaling with AI. 326+ reactions.$c$
WHERE full_name = $c$Nate Herkelman$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Nate Herkelman$c$, $c$Nate Herkelman$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 3] Scale Without Increasing Headcount (48K, Connect/Follow). Operators scaling with AI. 326+ reactions.$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t3-nate-herkelman$c$, ARRAY['influencer_v2','tier3']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Nate Herkelman$c$);

UPDATE contacts SET tags = array_append(COALESCE(tags, ARRAY[]::text[]), 'influencer_v2'),
  narration = COALESCE(narration, '') || $c$ | [Influencer List v2.0 TIER 3] Growth Architect for Service Businesses (nieznany, Follow/Connect). Aktywna wymiana pod Gary Vee. Czyste AGS ICP. Londyn UK. (dodany 25/04)$c$
WHERE full_name = $c$Dan O'Sullivan$c$ AND NOT ('influencer_v2' = ANY(COALESCE(tags, ARRAY[]::text[])));
INSERT INTO contacts (name, full_name, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Dan O'Sullivan$c$, $c$Dan O'Sullivan$c$, 'Peer', 'Watch (peer/competitor)', 'warm', 'Influencer List', $c$[Influencer List v2.0 TIER 3] Growth Architect for Service Businesses (nieznany, Follow/Connect). Aktywna wymiana pod Gary Vee. Czyste AGS ICP. Londyn UK. (dodany 25/04)$c$, 'AGS', $c$32ec00c90b93815ba73bf66c3adb20a3#t3-dan-osullivan$c$, ARRAY['influencer_v2','tier3']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Dan O'Sullivan$c$);

SELECT COUNT(*) AS contacts_total, COUNT(*) FILTER (WHERE 'influencer_v2' = ANY(tags)) AS influencers,
       COUNT(*) FILTER (WHERE 'crd_top15' = ANY(tags)) AS crd_top15 FROM contacts;
