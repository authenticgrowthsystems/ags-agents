-- TASK #71 FAZA D (05/07/2026): vendor_registry (Vendor Stack) + pricing_tiers AGS Premium.
-- Zrodla: Notion 357c00c90b9381f4a0e7f94147ba6bf0 (Vendor Stack cross-brand) + 34fc00c90b93817ca0d4c2269ebe6ca6 (doktryna Multi-Layer
-- Ecosystem v1.0-1.5 CANONICAL LOCKED). ROZJAZD $0/97/297/2K+ vs Tier1-4 = ROZWIAZANY:
-- jedna drabinka ags_premium, 7 wierszy (Warstwy 3/2/1; affiliate NIE jest tierem - decyzja
-- Tomasza guzikami 05/07); '$2K+' z kontraktu = Warstwa 1 (4 tiery Sales Bible).
-- Idempotentne: ON CONFLICT po kluczach naturalnych. AP-303: literaly dollar-quote.

INSERT INTO vendor_registry (vendor, category, brands, config, notes, notion_page_id)
VALUES ($v$seohost.pl$v$, $v$hosting_dns$v$, ARRAY[$v$TNM$v$, $v$RDC$v$, $v$PierwszyTaniec$v$, $v$LzA$v$, $v$AGS$v$]::text[],
  $v${"konto": "Tomasz Nawrocki", "hosting": "HOSTING NVMe 2024 (wygasa ~65 dni od 2026-05-05)", "domeny": [{"domain": "tyniemusisz.pl", "brand": "TNM", "wygasa": "2027-04-18", "email_lc": "TAK lc.tyniemusisz.pl GHL Mailgun"}, {"domain": "tyniemusisz.com", "brand": "TNM", "wygasa": "2027-04-18", "email_lc": "NIE"}, {"domain": "royaldance.pl", "brand": "RDC", "wygasa": "2027-01-04", "email_lc": "TAK ls.royaldance.pl GHL Mailgun ACTIVE default"}, {"domain": "royaldancecenter.pl", "brand": "RDC", "wygasa": "2027-04-20", "email_lc": "NIE"}, {"domain": "kursdolendance.pl", "brand": "RDC", "wygasa": "2026-10-26", "email_lc": "NIE"}, {"domain": "pierwszytaniecbezstresu.pl", "brand": "PierwszyTaniec", "wygasa": "2028-02-06", "email_lc": "CZESCIOWO (Inactive w GHL od 24/02, verify lub auto-delete po 03/06)"}, {"domain": "lysyzaparatem.pl", "brand": "LzA", "wygasa": "2026-10-26", "email_lc": "NIE"}, {"domain": "authenticgrowthsystems.com", "brand": "AGS", "wygasa": "2026-08-17", "email_lc": "NIE (AGS Mailgun bezposredni)"}], "affiliate": {"aktywacja_pct": 25, "odnowienie_pct": 15, "saldo": 0, "status": "unused"}, "support": "live chat panelu (Maciej Ignacyk sprawdzony 2026-05-05/15)"}$v$::jsonb, $v$Lesson 2026-05-05: MX records dla GHL Mailgun wymagaja FQDN z trailing dot (lc.domena.pl.), TXT/CNAME moga byc relative. Pattern: 6 rekordow DNS per sending domain.$v$, $v$357c00c90b9381f4a0e7f94147ba6bf0$v$)
ON CONFLICT (vendor, category) DO NOTHING;

INSERT INTO vendor_registry (vendor, category, brands, config, notes, notion_page_id)
VALUES ($v$GoHighLevel$v$, $v$crm_marketing$v$, ARRAY[$v$AGS$v$, $v$TNM$v$, $v$RDC$v$, $v$PierwszyTaniec$v$, $v$SdI$v$]::text[],
  $v${"subaccount": "Royal Dance Company Tomasz Nawrocki (shared multi-tenant)", "location_id": "FAxCpFiV8RrnzLTtpAZQ", "limitation": "domain config per SUB-ACCOUNT, nie per workflow (GHL support Meera A. 2026-05-15); wszystkie workflows wysylaja przez ls.royaldance.pl", "ags_rule": "AGS przy migracji na GHL Mailgun = OSOBNY sub-account, trigger $20K+ MRR (Q3 2026)", "isolation_pattern": "prefix brandu: display UPPERCASE (TNM_PL_Blueprint), technical lowercase (contact.tnm_*), dedykowany folder fields + pipeline + tagi per brand", "affiliate": {"recurring_pct": 40, "per_user_mies_usd": "39-119", "rola": "Warstwa 4 ekosystemu"}}$v$::jsonb, $v$Main CRM + email + SMS + landing platform. Bonus: GHL support otworzyl droge do custom API-level SMTP per workflow (deep dive pending od 2026-05-15).$v$, $v$357c00c90b9381f4a0e7f94147ba6bf0$v$)
ON CONFLICT (vendor, category) DO NOTHING;

INSERT INTO vendor_registry (vendor, category, brands, config, notes, notion_page_id)
VALUES ($v$Mailgun$v$, $v$email_delivery$v$, ARRAY[$v$TNM$v$, $v$RDC$v$, $v$AGS$v$]::text[],
  $v${"via": "GHL Email Services", "pattern": "6 rekordow DNS per sending domain, MX=FQDN", "ags": "Mailgun shared + GHL native do Q3 2026 (<50 emails/mc Stage 0-1)"}$v$::jsonb, $v$Migracja AGS na lc.authenticgrowthsystems.com gdy 500+ emails/mc lub potrzeba sender reputation isolation.$v$, $v$357c00c90b9381f4a0e7f94147ba6bf0$v$)
ON CONFLICT (vendor, category) DO NOTHING;

INSERT INTO vendor_registry (vendor, category, brands, config, notes, notion_page_id)
VALUES ($v$Cloudflare$v$, $v$cdn_hosting$v$, ARRAY[$v$AGS$v$]::text[],
  $v${"uwaga": "prawdopodobnie hosting GHL (162.159.140.166 = Cloudflare range)"}$v$::jsonb, $v$Affiliate opportunity US/UK relevant dla AGS (obok Vercel, Namecheap, Stripe).$v$, $v$357c00c90b9381f4a0e7f94147ba6bf0$v$)
ON CONFLICT (vendor, category) DO NOTHING;

INSERT INTO vendor_registry (vendor, category, brands, config, notes, notion_page_id)
VALUES ($v$n8n self-host$v$, $v$automation$v$, ARRAY[$v$AGS$v$, $v$TNM$v$, $v$RDC$v$]::text[],
  $v${"host": "mikrus.cloud", "rola": "transport automatyzacji, logika w Pythonie"}$v$::jsonb, NULL, $v$357c00c90b9381f4a0e7f94147ba6bf0$v$)
ON CONFLICT (vendor, category) DO NOTHING;

INSERT INTO vendor_registry (vendor, category, brands, config, notes, notion_page_id)
VALUES ($v$Notion$v$, $v$docs_ssot$v$, ARRAY[$v$AGS$v$, $v$TNM$v$, $v$RDC$v$, $v$SdI$v$, $v$LzA$v$]::text[],
  $v${"rola": "source of truth dla docs; po #71 = READ-ONLY MIRROR (cutover 08/07)"}$v$::jsonb, NULL, $v$357c00c90b9381f4a0e7f94147ba6bf0$v$)
ON CONFLICT (vendor, category) DO NOTHING;

INSERT INTO vendor_registry (vendor, category, brands, config, notes, notion_page_id)
VALUES ($v$Telegram Bot API$v$, $v$alerts_ui$v$, ARRAY[$v$AGS$v$]::text[],
  $v${"rola": "alerty + UI agentow (CM, Manager, Researcher)"}$v$::jsonb, NULL, $v$357c00c90b9381f4a0e7f94147ba6bf0$v$)
ON CONFLICT (vendor, category) DO NOTHING;

INSERT INTO vendor_registry (vendor, category, brands, config, notes, notion_page_id)
VALUES ($v$Twilio$v$, $v$sms$v$, ARRAY[$v$RDC$v$, $v$TNM$v$]::text[],
  $v${"via": "GHL"}$v$::jsonb, NULL, $v$357c00c90b9381f4a0e7f94147ba6bf0$v$)
ON CONFLICT (vendor, category) DO NOTHING;

-- ===== pricing_tiers: drabinka ags_premium (meta_status='active', decyzja Managera #2) =====

INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id, meta_status)
VALUES ('AGS', 'ags_premium', $p$free_guide$p$, $p$0$p$, 'USD',
  $p${"warstwa": 3, "layer": "mass_market_lead_magnet", "produkt": "DIY Guide: Build Your Expert Business Website in GHL (7 phases)", "gate": "GHL affiliate link registration (soft verification)", "status_build": "kompletny w Notion, wymaga affiliate link + PDF"}$p$::jsonb, $p$34fc00c90b93817ca0d4c2269ebe6ca6$p$, 'active')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id, meta_status)
VALUES ('AGS', 'ags_premium', $p$video_walkthrough$p$, $p$97$p$, 'USD',
  $p${"warstwa": 2, "layer": "productized_mid_tier", "produkt": "Video Walkthrough, 7 odcinkow 25-45 min", "status_build": "skrypt gotowy, czeka na nagranie (Loom 2-3h)"}$p$::jsonb, $p$34fc00c90b93817ca0d4c2269ebe6ca6$p$, 'active')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id, meta_status)
VALUES ('AGS', 'ags_premium', $p$dwy_bundle$p$, $p$297$p$, 'USD',
  $p${"warstwa": 2, "layer": "productized_mid_tier", "produkt": "Done-With-You: Guide + Video + 30-min review", "status_build": "koncepcja gotowa, wymaga GHL Checkout"}$p$::jsonb, $p$34fc00c90b93817ca0d4c2269ebe6ca6$p$, 'active')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id, meta_status)
VALUES ('AGS', 'ags_premium', $p$blueprint$p$, $p$2000$p$, 'USD',
  $p${"warstwa": 1, "layer": "premium_consulting", "sales_bible_tier": 1, "produkt": "Revenue Architecture Blueprint, 90-min strategic diagnostic", "status_build": "LIVE (/apply, GHL Survey 2-slide)"}$p$::jsonb, $p$34fc00c90b93817ca0d4c2269ebe6ca6$p$, 'active')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id, meta_status)
VALUES ('AGS', 'ags_premium', $p$aios_sprint$p$, $p$5000-8000$p$, 'USD',
  $p${"warstwa": 1, "layer": "premium_consulting", "sales_bible_tier": 2, "produkt": "AIOS Sprint (AI Operating System, 4 tyg)"}$p$::jsonb, $p$34fc00c90b93817ca0d4c2269ebe6ca6$p$, 'active')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id, meta_status)
VALUES ('AGS', 'ags_premium', $p$accelerator$p$, $p$15000$p$, 'USD',
  $p${"warstwa": 1, "layer": "premium_consulting", "sales_bible_tier": 3, "produkt": "Accelerator"}$p$::jsonb, $p$34fc00c90b93817ca0d4c2269ebe6ca6$p$, 'active')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id, meta_status)
VALUES ('AGS', 'ags_premium', $p$whale$p$, $p$50000-75000$p$, 'USD',
  $p${"warstwa": 1, "layer": "premium_consulting", "sales_bible_tier": 4, "produkt": "Whale engagement"}$p$::jsonb, $p$34fc00c90b93817ca0d4c2269ebe6ca6$p$, 'active')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

SELECT ladder, tier_name, price, meta_status FROM pricing_tiers ORDER BY ladder, tier_name;
SELECT vendor, category, array_length(brands,1) AS brands_n FROM vendor_registry ORDER BY vendor;
