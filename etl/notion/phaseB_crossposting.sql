-- TASK #71 FAZA B czesc 3: content_distribution_rules <- Cross-Posting Protocol v1.0 LEAN (05/07/2026).
INSERT INTO content_distribution_rules (brand_id, rule_name, content, config, notion_page_id)
SELECT 'AGS', 'Cross-Posting Protocol v1.0 LEAN TIER', 'Cross-Posting Protocol v1.0 LEAN TIER (29/05/2026). Status: Canonical, enforcement-ready. Owner: Manager AGS.
Audience: Manager TNM, Content Manager AGS, LinkedIn SM, Content Engine, AA TNM, WEBSITE & FUNNELS.

TIER 1: ENFORCE NOW (5 rules, zero overhead, Stage 0-1 safe)
Rule 1: PL vs EN audience separation. TNM (PL) content NEVER raw na AGS (EN); AGS (EN) never raw na TNM (PL);
Personal Tomasz = uniwersalny bridge (multi-lingual OK na personal).
Rule 2: Down-share company to personal MUSI miec commentary (1-3 zdania wlasnego commentary przy kazdym re-share;
bez commentary = dummy share = algorithm penalty).
Rule 3: Zero raw cross-post, adapted format per platform (LinkedIn Carousel -> X Thread = adapted hooks per tweet;
LinkedIn long-form -> X long-form premium lub thread; never raw copy-paste).
Rule 4: Timing match per audience. US/UK/CA: 16:00-17:00 CET (=10:00-11:00 EST peak); Polish: 08:30 CET;
International mixed: 12:00-14:00 CET overlap.
Rule 5: Cross-channel sequence TYLKO dla anchor pieces (anchor = lead magnet ship, flagship karuzela, newsletter,
content product launch; sequence: T+0 / T+24h personal share / T+48h cross-brand / T+1 tydzien backlog;
feed posts = single-channel OK).

TIER 2: PARKED do post-pierwsza-sprzedaz (cum reach analytics, 14-day rolling lift, cross-brand attribution,
Quadruple Proof dashboard). Trigger reaktywacji: M5 First Client closed lub TNM first Plan dzialania sale.

RESPONSIBILITY: Content Manager AGS = master orchestrator (audit per 5 rules przed publish); LinkedIn SM =
secondary shares T+24h dla anchors; Manager TNM = TNM compliance; Content Engine = produkcja z cross-posting
awareness; AA TNM / WEBSITE & FUNNELS = follow protocol.

TOP 5 NEVER-DO: 1) never raw cross-post TNM(PL)<->AGS(EN); 2) never down-share bez 1-3 zdan commentary;
3) never raw LinkedIn->X (always adapt); 4) never same content 3+ razy/tydzien; 5) never publikuj w godzinach
gdzie audience nie uzywa platformy.

ICP ROUTING: US/UK/CA premium founder ($2K+) -> AGS + Personal EN; Polish SMB (TNM $1-3K) -> TNM + Personal PL;
Wedding couple PL -> Pierwszy Taniec + RDC LinkedIn; Dance student PL -> RDC; AI/tech curious EN -> AGS +
Personal EN + X; AI/tech curious PL -> TNM + Personal PL.

GOVERNANCE: v1.0 LEAN 29/05/2026; owner Manager AGS; review trigger = M5 lub TNM first sale; full enterprise
version w workspace AGS_CrossPosting_Protocol_v1.md (future reference post-M5).',
'{"tier1_rules": [{"rule": 1, "name": "pl_en_separation", "desc": "TNM PL nigdy raw na AGS EN i odwrotnie; personal = bridge"}, {"rule": 2, "name": "downshare_commentary", "desc": "re-share company->personal wymaga 1-3 zdan commentary"}, {"rule": 3, "name": "no_raw_crosspost", "desc": "zawsze adaptacja formatu per platforma"}, {"rule": 4, "name": "timing_per_audience", "windows": {"us_uk_ca": "16:00-17:00 CET", "pl": "08:30 CET", "mixed": "12:00-14:00 CET"}}, {"rule": 5, "name": "sequence_for_anchors_only", "sequence": ["T+0", "T+24h personal", "T+48h cross-brand", "T+7d backlog"]}], "never_do": ["raw TNM<->AGS", "downshare bez commentary", "raw LinkedIn->X", "same content 3+/tydzien", "publikacja poza godzinami audience"], "icp_routing": {"us_premium_founder": ["AGS", "personal_en"], "pl_smb": ["TNM", "personal_pl"], "wedding_pl": ["PierwszyTaniec", "RDC_linkedin"], "dance_student_pl": ["RDC"], "ai_curious_en": ["AGS", "personal_en", "x"], "ai_curious_pl": ["TNM", "personal_pl"]}, "tier2_parked_trigger": "M5 first client OR TNM first sale"}'::jsonb, '370c00c90b938110a1d2cb9edfc04f0e'
WHERE NOT EXISTS (SELECT 1 FROM content_distribution_rules WHERE notion_page_id = '370c00c90b938110a1d2cb9edfc04f0e');

SELECT rule_name, length(content) AS len FROM content_distribution_rules;
