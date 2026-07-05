# Anti-Pattern Library

Lessons learned across all AGS agents. Each entry: anti-pattern + why bad + correct alternative.

Agents must screen output against this library BEFORE HITL preview.

---

## Voice / Conversation Anti-Patterns (from Pawel Voice Agent tests #1-7)

### AP-001: Hallucinating actions you don't have
**Anti-pattern:** "Wyślę Panu SMS-a z potwierdzeniem" when no SMS workflow exists.
**Why bad:** Customer waits for SMS that never arrives. Trust killer.
**Correct:** "Tomasz oddzwoni najszybciej jak to możliwe. Zapisałem Pana dane."

### AP-002: Information dump on closed questions
**Anti-pattern:** Customer asks "Czy macie półkolonie?" → Agent gives 8-sentence lecture on dates, prices, program, age groups.
**Why bad:** Closed question wants Yes/No + qualifying question, not unsolicited deep dive.
**Correct:** "Tak, mamy. Dla jakiego dziecka?" Max 2 sentences. Let customer drive depth.

### AP-003: Hallucinating offering names
**Anti-pattern:** Inventing classes like "Hip Hop Juniorzy" when KB lists "Hip-Hop dla Dzieci (8-12 lat)".
**Why bad:** Customer expects offering that doesn't exist. Trust + brand consistency damage.
**Correct:** Use exact KB names. If category not in KB: "Tej kategorii nie mamy. Tomasz oddzwoni z propozycją alternatywy."

### AP-004: Continuing conversation after farewell
**Anti-pattern:** After saying "Dziękuję za telefon, do usłyszenia" - agent adds "Czy mogę kontynuować?"
**Why bad:** Logical drift. Disrespects customer's signal that they're done.
**Correct:** After farewell = END. No more questions, no more topics.

### AP-005: Reading domain names literally
**Anti-pattern:** "Proszę wejść na royaldance.pl" (TTS pronounces poorly).
**Why bad:** TTS distortion makes customer think you said something else.
**Correct:** "Nasza strona internetowa" or "przez naszą stronę". Only literal if customer explicitly asks for URL.

### AP-006: Phone numbers grouped wrong
**Anti-pattern:** "sześćset dwadzieścia, dwa dziewięć, osiemset pięćdziesiąt cztery" (grouping into numbers).
**Why bad:** Customer can't follow / verify. Polish mobile is 9 digits in 3+3+3 pattern.
**Correct:** Single digit per beat with pauses. "sześć, dwa, zero. [pauza] dwa, dziewięć, osiem. [pauza] pięć, cztery, dziewięć"

### AP-007: Price-first communication
**Anti-pattern:** "Pakiet Premium kosztuje 1990 zł. W nim 8 spotkań."
**Why bad:** Customer hears price before understanding value. Defensive reaction.
**Correct:** "Para przed weselem ma 3 miesiące, pierwszy raz tańczy. Rozwiązanie: 8 spotkań, montaż muzyki, próba na sali. Rezultat: pewność na parkiecie. Inwestycja: tysiąc dziewięćset dziewięćdziesiąt złotych."

### AP-008: "Bezpłatne" instead of "niezobowiązujące"
**Anti-pattern:** "Pierwsze zajęcia są bezpłatne."
**Why bad:** If customer stays, first class becomes part of monthly fee - "bezpłatne" was technically misleading.
**Correct:** "Pierwsze zajęcia są niezobowiązujące."

---

## Content Anti-Patterns (from 23 Manager chats + brand canon learnings)

### AP-101: Em dashes
**Anti-pattern:** Using em dash (—) anywhere in any AGS content.
**Why bad:** Tomasz brand canon RULE 1.
**Correct:** Hyphen, restructure sentence, or use colon.

### AP-102: Empty enthusiasm vocabulary
**Anti-pattern:** "Fantastycznie!", "Wspaniale!", "Doskonale!", "Świetnie się składa!"
**Why bad:** Empty filler, doesn't convey real reaction, sounds AI-generated or corporate.
**Correct:** "Super.", "Dobrze.", "Jasne.", "Rozumiem."

### AP-103: Promising scarcity that doesn't exist
**Anti-pattern:** "Tylko 3 miejsca zostały!" when no inventory check happened.
**Why bad:** Fake urgency damages brand long-term.
**Correct:** State real availability or skip urgency.

### AP-104: Generic stock photos in content
**Anti-pattern:** Using stock founder photos / generic AI workspace shots for AGS content.
**Why bad:** AGS positioning is "real builds in public" - stock images undermine authenticity.
**Correct:** Real screenshots from current builds, raw phone photos, even messy whiteboards.

---

## Strategic Anti-Patterns

### AP-201: System-building before understanding what produces revenue
**Anti-pattern:** Spending weeks on infrastructure that doesn't connect to client conversion.
**Why bad:** Stage 0-1 + Hormozi 10-Stage doctrine.
**Correct (pre-19/05):** "No system building before first sale."
**Correct (post-19/05 pivot):** "System building IS content IS revenue activity - but only when build is documented in public AND links to ICP attraction."

### AP-202: Lowering price after customer says no
**Anti-pattern:** "Premium is 1990 zł. (customer hesitates) Actually I can do 1500 zł for you."
**Why bad:** Trains customer to push back on every price. Damages anchor.
**Correct:** Down-tier to a different package (Startowy 880 zł) instead of discounting same package.

### AP-203: Maintaining 50 KPIs
**Anti-pattern:** Dashboard with 30+ metrics nobody acts on.
**Why bad:** Cognitive overhead, dilutes focus, paralyzes action.
**Correct:** Max 3 KPIs per stage. Default: Revenue (closed $), Pipeline (calls booked), Close rate (%).

### AP-301: New n8n node with typeVersion from memory instead of from a working sibling
**Anti-pattern (03/07/2026, BE, HITL 1b build):** created two IF nodes with `typeVersion: 1` but NEW filter-format conditions. Old IF engine ignores the unknown format and passes EVERYTHING true - the agent router silently sent all text to Idea Bot and (worse) the agsel gate swallowed ALL callback families, killing approve/triage buttons until hotfix.
**Why bad:** silent pass-through, no error anywhere; discovered only in Tomasz's tap-test; every broken production window costs trust and money.
**Correct:** when adding a node to an existing workflow, COPY typeVersion + parameter shape from a WORKING node of the same type in that workflow (e.g. `Is Cm Callback?` = if 2.2, conditions.options {version:2, typeValidation:'loose'}). Verify routing with a real execution read (executions API, node-by-node), not only structure.

### AP-303: SQL string literals in generated ETL without dollar-quoting
**Anti-pattern (05/07/2026, BE, #71 Faza B):** generator built an INSERT with a Polish doctrine text embedded via `'...'` and manual `''` escaping of only SOME apostrophes - the canonical-bio INSERT failed live (`syntax error at or near "choreograf"`) while 20 sibling INSERTs (escaped via helper) passed, so the miss was silent until psql output was read line-by-line.
**Why bad:** hand-escaping free text is guaranteed to miss quotes eventually; a failed statement inside a multi-statement file does NOT stop the file, so partial loads look successful.
**Correct (canonical, Manager 05/07 - applies to ALL future AGS/client migrations and ETL):** EVERY free-text literal in generated SQL goes through dollar-quoting (`$tag$...$tag$` with an `assert tag not in text` guard) or bind parameters; never hand-escaped quotes. Verify loads by row-count SELECT, not by absence of visible errors.

### AP-302: User-facing vocabulary invented by the agent without checking brand register
**Anti-pattern (03/07/2026):** BE named the inspirations pool "zanadrze" in bot replies and tool names. Tomasz: "na pewno nie bedziemy tego slowa uzywac".
**Why bad:** user-facing wording is brand voice territory; archaic/bookish words break the operator register.
**Correct:** for user-facing labels pick plain everyday Polish ("schowek", "baza"), confirm with Tomasz when introducing a NEW recurring label.

---

## How to add entries

When agents fail in production OR Tomasz catches an issue during HITL review:

1. Add new entry with next sequential AP-XXX number (AP-001 series for voice, AP-100 for content, AP-200 for strategic)
2. Date the entry
3. Reference the agent + session where it was caught
4. Update relevant agent's prompt to explicitly prevent this pattern
