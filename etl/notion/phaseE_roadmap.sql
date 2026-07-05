-- TASK #71 FAZA E (05/07/2026): roadmap_milestones <- AGS Roadmap (Notion 318c00c90b93812f9cf8f6e78c33ee7a,
-- stan = pelny refresh Managera 14/05/2026). 16 kamieni. Idempotentne po entry_hash.
-- AP-303 dollar-quote; M3.7 = brand TNM (scope TNM wg strony).

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M0 Fundament$r$, $r$critical_path$r$, NULL, 'done', $r$Context OS AGS (7 dokumentow), Notion workspace, Pareto Pricing Framework, offer ladder 4 tiery, architektura 6 agentow, Post #1. DONE 26/02-03/03.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, 'd6524e07d512e9949aaf36053045bd81')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M1 Case Study #1$r$, $r$critical_path$r$, NULL, 'in_progress', $r$REROUTED 14/05: case study = pierwszytaniecbezstresu.pl (przetestowane na sobie, 5 par slubnych, GA4+GSC+Ads). SdI schodzi z bramki. Zostalo: dokumentacja BEFORE/AFTER + SOP. Bramka do M2: min. 3 AFTER datapoints (sa) + dokumentacja.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, '8e98d006d91e7a04830218812860f05a')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M2 Krystalizacja oferty$r$, $r$critical_path$r$, NULL, 'done', $r$Offer ladder 4 tiery LOCKED: Blueprint $2K, AIOS Sprint $5-8K, Accelerator $15K, Whale $50-75K + mid-tier Video $97 / DWY $297. SOP delivery AIOS dokonczony z doswiadczenia M5.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, '0ce8d073f9e3f432baa2e1d632568fda')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M3 Strona + funnel$r$, $r$critical_path$r$, NULL, 'done', $r$DONE 27/04: 5 stron live w GHL, SSL, GSC, sitemap, GA4, Follow-up+SMS, Chatbot Faza A (0 violations). Faza B chatbota = post-M5.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, 'ea27de0a22a09429463a83cce89a875d')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M4a LinkedIn outreach$r$, $r$critical_path$r$, NULL, 'in_progress', $r$Rownolegle z M1. Connection requesty ICP, DM-y, posty, Comment Radar SOP v1.0. KPI: 100+ conn/tydz, 25+ DM/tydz, 10+ rozmow, 3-5 calli. Content: mowimy prawde, zero obietnic bez pokrycia.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, '60b1b5aa44a735673cc1e4469a53769f')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M4b Content funnel$r$, $r$critical_path$r$, NULL, 'locked', $r$Email nurture, lead magnet funnel, calendar z CTA, retargeting. Bramka do M5: 5 Blueprint Calls zarezerwowanych.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, '00db07bf15c02bbe9bec76ff6e827cc8')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M5 Pierwszy zewnetrzny klient$r$, $r$critical_path$r$, NULL, 'active', $r$PRIORYTET 1 (stage 0-1). 1-2 klientow Blueprint $2K -> sciezka do AIOS. Tracye Warfield COLD/GHOST od 05/05; zrodla: Manus V1/V2, MMI/GBI od 19/05, inbound /apply. Bramka do M6: 1 klient zaplacil + delivery done.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, '0f9eeddb9601776d91245fe88ecd30f3')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M6 Optymalizacja$r$, $r$critical_path$r$, NULL, 'locked', $r$Case study #2, ladder skalibrowany close rate, Accelerator $15K sellable, VA/Marketing Generalist, Rule of 100.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, '404a09a5c61ed163e2283c5b1426a8bc')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M3.5 Mid-tier funnel$r$, $r$ecosystem_4layer$r$, NULL, 'in_progress', $r$Video $97 + DWY $297 + Affiliate Gate System. Priorytet po Wave 0.5. Czesc 4-Layer Ecosystem Doctrine.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, 'e0a46b858300176bd06f1c5f004085d0')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M3.6 Newsletter AGS Weekly Intel$r$, $r$ecosystem_4layer$r$, NULL, 'planning', $r$GHL Native (NIE Beehiiv - override Tomasza). Parallel track, zero website work.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, 'dde000a1135b4f30b4785e72303caee0')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('TNM', $r$M3.7 TNM EU AI Act Starter Kit$r$, $r$tnm$r$, '2026-08-02', 'planning', $r$Scope TNM (nie AGS). Soft launch 1/07/2026, hard deadline 2/08/2026 (enforcement EU AI Act). Koordynuje Manager TNM.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, '91976c865089c91e7590fa20d14e0c2a')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M3.8 Niche Affiliate Funnel$r$, $r$ecosystem_4layer$r$, NULL, 'planning', $r$10 branz parallel test (czerwiec-sierpien). Niche-specific qualified outbound: GHL Survey + tier matching (doktryna v1.5). Niche Vault DB: 353c00c90b9381c880d3e14a2aa409f6.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, '3db848af4800a76c702979870a71c7a8')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M6.0 90-Day Flywheel Ignition$r$, $r$post_m5$r$, '2026-06-01', 'locked', $r$Bramka: M5 done + Wave 0.5 + Niche Vault locked.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, '86ed8abea22993b7dafd5a3a3197e6b1')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M6.1 Pozycjonowanie evolution$r$, $r$post_m5$r$, NULL, 'locked', $r$'Multi-Agent Operating Architect' - ewolucja pozycjonowania po pierwszym kliencie (doktryna v1.4 Amendment B).$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, 'b7282b7351093eaf121a82d752e26177')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M6.3 Agent-to-Agent logging channel$r$, $r$post_m5$r$, NULL, 'locked', $r$Agenci komunikuja sie przez wspolna baze - Tomasz przestaje byc message routerem. Post-Wave 0.5, AA AGS.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, 'e4cc76e1451e6758b22375fe41d698e5')
ON CONFLICT (entry_hash) DO NOTHING;

INSERT INTO roadmap_milestones (brand_id, milestone, campaign, due_date, status, details, notion_page_id, entry_hash)
VALUES ('AGS', $r$M7 Foreign company decision$r$, $r$post_m5$r$, NULL, 'locked', $r$Trigger: pierwszy klient US. PL JDG ryczalt 12% vs Wyoming LLC 30 dni. Manager AGS + Financial Advisor.$r$, $r$318c00c90b93812f9cf8f6e78c33ee7a$r$, 'c33a287aab3e00c92c0deecd97ae651c')
ON CONFLICT (entry_hash) DO NOTHING;

SELECT brand_id, milestone, status, campaign FROM roadmap_milestones ORDER BY milestone;
