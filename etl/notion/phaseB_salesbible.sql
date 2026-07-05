-- TASK #71 FAZA B czesc 5: sales_playbook <- Sales Bible v0.2 (decyzja Managera #1: content=PELNY plik
-- workspace SALES_BIBLE.md, mirror=strona Notion). Idempotentne.
INSERT INTO sales_playbook (brand_id, section, title, content, version, notion_page_id)
SELECT 'AGS', 'sales_bible', 'AGS Sales Bible v0.2 (D1-D19 + Canonical Truth + Messaging + Outreach)',
$n71$# AGS Sales Bible v0.2 — Controlled Draft
## Status: WORKING DRAFT | Created: 10/03/2026 | Owner: MANAGER

Sources: Alex Hormozi, Myron Golden, Blair Enns, Chris Voss
Rule: Each section labeled: SALES DOCTRINE / CANONICAL / IMPLEMENT NOW / PARKING LOT / REQUIRES VALIDATION

---

## PART 1: SALES DOCTRINE (19 entries)

### D1. Obsession with Their Problems, Not Your Need to Close
Source: Myron Golden | IMPLEMENT NOW
Every DM, every post, every call — 100% about THEIR chaos. Zero "I have a great product." Ask diagnostic questions, not pitch.

### D2. Never Reveal Price Before Value
Source: Myron Golden + Hormozi | IMPLEMENT NOW
Price without context is always "too much." Value must be stacked BEFORE price is mentioned.

### D3. Sell Payoff, Not Pieces
Source: Myron Golden + Hormozi | IMPLEMENT NOW
People don't buy 6 AI agents. They buy: content that runs itself, leads followed up at 2am, 20 hours/week back.

### D4. Value Equation (Hormozi)
Value = (Dream Outcome x Perceived Likelihood) / (Time Delay x Effort & Sacrifice)
AGS AIOS Sprint scores high on dream outcome + speed + low effort. BUT: Perceived Likelihood is LOW (zero proof). Fix with M1 case study.

### D5. Seamless Selling
Source: Myron Golden | IMPLEMENT NOW
Don't convince. Don't pressure. Create environment where prospect SEES the transformation.

### D6. Time > Money
Source: Myron Golden | IMPLEMENT NOW
ICP founders already have money. Sell TIME RECOVERY, not cost savings. "Recover 20 hours/week."

### D7. Serve-First Outreach
Source: Myron Golden | IMPLEMENT NOW
Build pipeline with no audience, no list, no budget. Be a resource. Comment helpfully. Get noticed by being valuable.

### D8. High-Profit x Low Volume
Source: Myron Golden | IMPLEMENT NOW
You need 2-3 clients/month at high margin, not 100 at low margin.

### D9. Price = Communication of Value
Source: Hormozi | IMPLEMENT NOW
Low price = signal of low quality. Premium buyers sort high-to-low. "Fortunately, it's expensive."

### D10. Close Rate as Pricing Diagnostic
Source: Hormozi | REQUIRES VALIDATION
60-80% = price 3-4x too low. 30-40% = price OK. Below 30% = problem with offer.
AGS status: ZERO close rate data. Requires min 10 conversations.

### D11. Specialize or Be Commoditized
Source: Blair Enns | IMPLEMENT NOW
Don't be "an AI agency." Be "the system architect for creative founders who refuse to sound like robots."

### D12. The Sale Is the Sample of the Engagement
Source: Blair Enns | IMPLEMENT NOW
How you sell is a preview of how you deliver. Show up as expert advisor, not desperate vendor.

### D13. Don't Give Away Thinking for Free
Source: Blair Enns | IMPLEMENT NOW
Free audits = training market that your expertise has no value. Blueprint ($2,000) is a PAID entry point.

### D14. Podcast Outreach = Unfair Advantage
Source: Myron Golden | PARKING LOT
Activate after M1 complete + 1-2 external clients.

### D15. Volume x Leverage = Output
Source: Hormozi | IMPLEMENT NOW
Rule of 100: 100 minutes marketing/day. AI multiplies output but doesn't replace daily discipline.

### D16. If Referrals Aren't #1 Source, Product Isn't Good Enough Yet
Source: Hormozi | REQUIRES VALIDATION
Zero clients = zero referrals. Perfect delivery before scaling.

### D17. Tactical Empathy
Source: Chris Voss | IMPLEMENT NOW
Mirroring, Labeling, Calibrated Questions, "That's Right", Accusation Audit.

### D18. Don't Compromise — Find the Black Swan
Source: Chris Voss | IMPLEMENT NOW
When prospect says "too expensive": Mirror > Label > Calibrated question. Don't lower price.

### D19. 75/15 Marketing Method
Source: APEX | IMPLEMENT NOW
75% derivatives of what works. 15% R&D (new channels). 10% rest.
AGS: 75% = LinkedIn posts + DM outreach. 15% = Influencer commenting. Rest = PARKING LOT.

---

## PART 2: CANONICAL AGS TRUTH

- Stage: 0-1 (Monetize)
- Revenue: $0
- Paying clients: 0
- Case studies: 1 internal (SdI, incomplete)
- Tiers: Blueprint $2K | AIOS Sprint $5-8K | Accelerator $15K | Whale $50-75K
- CTA: Manual DM scheduling (no Calendly, no /apply yet)

---

## PART 3: MESSAGING RULES

### Website: Zero public pricing. CTA = qualification/application. Cost of inaction section mandatory.
### DMs: Never open with what you sell. Open with what you NOTICED. Peer-to-peer tone.
### Follow-ups: Each touch adds value. 48h / 5d / 8d sequence. Archive after 3 no-responses.
### Calls: Blair Enns 4 Conversations + Hormozi price anchoring + Voss tactical empathy.

---

## PART 4: FORBIDDEN IN ALL COMMUNICATIONS

- Never claim AGS has paying clients
- Never claim specific ROI results
- Never use fake testimonials
- Never reference /apply page (doesn't exist yet)
- Never use "Book your Blueprint Call"
- Never mention Calendly
- Never ask coaches/consultants about their clients (ethics violation)
- Never start DMs with "Glad we're connected!"
$n71$, '0.2', '31fc00c90b938114be2cf25c4041edbb'
WHERE NOT EXISTS (SELECT 1 FROM sales_playbook WHERE notion_page_id = '31fc00c90b938114be2cf25c4041edbb');

SELECT section, version, length(content) AS len FROM sales_playbook;
