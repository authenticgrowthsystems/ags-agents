-- TASK #71 C-uzupelnienie (05/07): chat_registry + kandydaci Founders List -> contacts.
-- USTALENIE audit-first: 'AGS FOUNDERS LIST' = INSTRUKCJA metodyczna (10 krokow), nie lista kontaktow;
-- metodologia idzie do sales_playbook (silnik), tu wchodzi 5 kandydatow z werdyktami.

INSERT INTO chat_registry (instance_name, platform, purpose, config, notion_page_id)
SELECT $c$MANAGER (Cowork)$c$, 'claude', $c$Strategia, koordynacja, Sales Bible, copy, Notion, canonical truth enforcement$c$, $c${"model": "Opus", "status": "active", "mode": "full_authority"}$c$::jsonb, $c$31fc00c90b9381078595cfa7451596f6#manager-cowork$c$
WHERE NOT EXISTS (SELECT 1 FROM chat_registry WHERE notion_page_id = $c$31fc00c90b9381078595cfa7451596f6#manager-cowork$c$);

INSERT INTO chat_registry (instance_name, platform, purpose, config, notion_page_id)
SELECT $c$LinkedIn Sales Manager v2.0$c$, 'claude', $c$Connection notes, DMs, follow-upy, pipeline, Lead Tracker$c$, $c${"model": "Sonnet", "status": "active", "mode": "needs_doctrine_sync"}$c$::jsonb, $c$31fc00c90b9381078595cfa7451596f6#linkedin-sales-manager-v20$c$
WHERE NOT EXISTS (SELECT 1 FROM chat_registry WHERE notion_page_id = $c$31fc00c90b9381078595cfa7451596f6#linkedin-sales-manager-v20$c$);

INSERT INTO chat_registry (instance_name, platform, purpose, config, notion_page_id)
SELECT $c$Website & Funnels$c$, 'claude', $c$GHL build, QA, implementation support$c$, $c${"model": "Sonnet", "status": "active", "mode": "implementation_only_no_strategy"}$c$::jsonb, $c$31fc00c90b9381078595cfa7451596f6#website-&-funnels$c$
WHERE NOT EXISTS (SELECT 1 FROM chat_registry WHERE notion_page_id = $c$31fc00c90b9381078595cfa7451596f6#website-&-funnels$c$);

INSERT INTO chat_registry (instance_name, platform, purpose, config, notion_page_id)
SELECT $c$LinkedIn Profile Architect$c$, 'claude', $c$Audyt/optymalizacja profilu, SEO, doctrine compliance, metryki (SSI baseline=39)$c$, $c${"model": "Opus", "status": "active", "mode": "reporting_to_manager"}$c$::jsonb, $c$31fc00c90b9381078595cfa7451596f6#linkedin-profile-architect$c$
WHERE NOT EXISTS (SELECT 1 FROM chat_registry WHERE notion_page_id = $c$31fc00c90b9381078595cfa7451596f6#linkedin-profile-architect$c$);

INSERT INTO chat_registry (instance_name, platform, purpose, config, notion_page_id)
SELECT $c$Content Engine v2.0$c$, 'claude', $c$Produkcja postow (#8-#17 delivered)$c$, $c${"model": "-", "status": "frozen", "mode": "freeze_until_review"}$c$::jsonb, $c$31fc00c90b9381078595cfa7451596f6#content-engine-v20$c$
WHERE NOT EXISTS (SELECT 1 FROM chat_registry WHERE notion_page_id = $c$31fc00c90b9381078595cfa7451596f6#content-engine-v20$c$);

INSERT INTO chat_registry (instance_name, platform, purpose, config, notion_page_id)
SELECT $c$Research Lab$c$, 'claude', $c$Research ad-hoc (outputy w Notion)$c$, $c${"model": "-", "status": "frozen", "mode": "open_new_when_needed"}$c$::jsonb, $c$31fc00c90b9381078595cfa7451596f6#research-lab$c$
WHERE NOT EXISTS (SELECT 1 FROM chat_registry WHERE notion_page_id = $c$31fc00c90b9381078595cfa7451596f6#research-lab$c$);

INSERT INTO chat_registry (instance_name, platform, purpose, config, notion_page_id)
SELECT $c$Archiwum 01 - MANAGER$c$, 'claude', $c$Stara instancja Managera (saturated, superseded)$c$, $c${"model": "Opus", "status": "frozen", "mode": "superseded"}$c$::jsonb, $c$31fc00c90b9381078595cfa7451596f6#archiwum-01---manager$c$
WHERE NOT EXISTS (SELECT 1 FROM chat_registry WHERE notion_page_id = $c$31fc00c90b9381078595cfa7451596f6#archiwum-01---manager$c$);

INSERT INTO chat_registry (instance_name, platform, purpose, config, notion_page_id)
SELECT '_ownership_rules', 'claude', 'Macierz wlasnosci domen miedzy czatami (11/03, update 20/03)', $c${"sales_bible": {"owner": "MANAGER", "never": "any other chat"}, "offer_truth": {"owner": "Notion canonical + MANAGER + ChatGPT + Tomasz", "never": "any Claude chat independently"}, "website_strategy": {"owner": "LOCKED (Website Canon Index)", "never": "anyone"}, "website_implementation": {"owner": "Website & Funnels"}, "copy_positioning": {"owner": "MANAGER", "never": "Content Engine, LinkedIn SM"}, "dm_execution": {"owner": "LinkedIn SM", "never": "MANAGER (strategy only)"}, "canonical_truth": {"owner": "Notion (record) + MANAGER (enforcer)", "never": "individual agent chats"}, "linkedin_profile": {"owner": "Profile Architect", "never": "Content Engine, LinkedIn SM"}}$c$::jsonb, $c$31fc00c90b9381078595cfa7451596f6#ownership$c$
WHERE NOT EXISTS (SELECT 1 FROM chat_registry WHERE notion_page_id = $c$31fc00c90b9381078595cfa7451596f6#ownership$c$);

INSERT INTO contacts (name, full_name, x_handle, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Eiran Trethowan$c$, $c$Eiran Trethowan$c$, $c$@SoloBoardroom$c$, 'Cold', 'Watch', 'founders_candidate', 'Unknown', $c$[Founders List kandydat #10 kroku] STRONG candidate (verified, mutual follow, 'Business Systems Architect, solo parent, SOLO:BOARDROOM'). Geo-check: jesli AU/NZ -> ADD.$c$, 'AGS', $c$353c00c90b9381569394f780eabd10ac#cand-soloboardroom$c$, ARRAY['x_founders_candidate']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Eiran Trethowan$c$);

INSERT INTO contacts (name, full_name, x_handle, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Greg Miller$c$, $c$Greg Miller$c$, $c$@gregmillerai$c$, 'Cold', 'Watch', 'founders_candidate', 'Unknown', $c$[Founders List kandydat #10 kroku] Borderline ('Building software that lets YOU build software', intrinsic-labs.ai). Jesli service-led founder -> ADD; jesli SaaS -> skip.$c$, 'AGS', $c$353c00c90b9381569394f780eabd10ac#cand-gregmillerai$c$, ARRAY['x_founders_candidate']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Greg Miller$c$);

INSERT INTO contacts (name, full_name, x_handle, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$ListClose$c$, $c$ListClose$c$, $c$@ListClose$c$, 'Cold', 'Watch', 'founders_candidate', 'Unknown', $c$[Founders List kandydat #10 kroku] STRONG (real estate service, 'List your home, save thousands, 2% back'). Geo-check przed ADD.$c$, 'AGS', $c$353c00c90b9381569394f780eabd10ac#cand-listclose$c$, ARRAY['x_founders_candidate']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$ListClose$c$);

INSERT INTO contacts (name, full_name, x_handle, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Jhulan Dey$c$, $c$Jhulan Dey$c$, $c$@JDAutoPilot$c$, 'Cold', 'Watch', 'founders_candidate', 'Unknown', $c$[Founders List kandydat #10 kroku] Zwalidowany PEER (Content & Automation) - do listy Peers, NIE Founders.$c$, 'AGS', $c$353c00c90b9381569394f780eabd10ac#cand-jdautopilot$c$, ARRAY['x_founders_candidate']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Jhulan Dey$c$);

INSERT INTO contacts (name, full_name, x_handle, status, icp_tier, pipeline_stage, source, narration, brand_affinity, notion_page_id, tags)
SELECT $c$Marcos Talon$c$, $c$Marcos Talon$c$, $c$@MarcosTalon$c$, 'Cold', 'Watch', 'founders_candidate', 'Unknown', $c$[Founders List kandydat #10 kroku] Recurring engagement (sub-reply pod Hormozim, reciprocal like). Profile-check: service founder -> ADD, solo creator -> Peers.$c$, 'AGS', $c$353c00c90b9381569394f780eabd10ac#cand-marcostalon$c$, ARRAY['x_founders_candidate']
WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE full_name = $c$Marcos Talon$c$);

SELECT 'chat_registry' AS t, COUNT(*) AS n FROM chat_registry
UNION ALL SELECT 'contacts_total', COUNT(*) FROM contacts
UNION ALL SELECT 'founders_cand', COUNT(*) FROM contacts WHERE 'x_founders_candidate' = ANY(tags);
