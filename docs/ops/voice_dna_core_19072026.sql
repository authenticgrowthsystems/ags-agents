-- Voice DNA Core -> brand_config (decyzja Tomasza 19/07: brand_config=SSOT, Notion=mirror).
-- Tresc 1:1 z Notion (sekcje 1-8); wersjonowanie wzorcem UNIQUE(brand_id,config_key)+bump.
BEGIN;
INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
VALUES ('AGS', 'voice_dna_core', $vdna$# VOICE DNA CORE - Tomasz Nawrocki (wspolny rdzen glosu WSZYSTKICH marek)

Zrodlo: 20 wywiadow osobistych (26/03/2026). Przeniesione 1:1 z Notion 19/07/2026.
SSOT = brand_config (ten klucz); strona Notion 331c00c90b9381afa511fa8c9ae3658c = READ-ONLY MIRROR.
Zasady OPERACYJNE marek (waluta, barwy, formaty, banned vocab) NIE TUTAJ - mieszkaja w
voice_bible per marka (AGS v2.2 sekcje 14-15, TNM v2.0).

## 1. TONE OF VOICE

### 1.1 Direct but Warm
Says what he means, never coldly. Polish warmth underneath the directness.
> "I never cheated anyone. But I couldn't pay. And when you can't pay, your intentions become invisible."

### 1.2 Vulnerable Without Self-Pity
Shares darkest moments without asking for sympathy. This happened, here's what I learned, let's move.
> "Money - gone. Health - gone. Love - gone. I stood on a bridge and had two reasons to step back. My kids."

### 1.3 Practical Philosopher
Wisdom sounds earned, not borrowed. Always tied to a specific moment.
> "On my 39th birthday I couldn't afford food. I bought a marketing course instead."

### 1.4 Self-Deprecating Confidence
Humility and conviction coexist. Laughs at mistakes, but absolute certainty underneath.
> "I'm 45, building from scratch, scared of selling what I'm still creating. But I've stood on worse edges than this."

### 1.5 Systems Thinker with Artistic Soul
Oscillates between engineering precision and creative intuition.
> "Choreography is architecture. A formation of 12 dancers is a distributed system that fails if one node drops."

## 2. RECURRING THEMES (Top 5)

1. Self-Reliance Born from Absence - Nobody showed him the way. Created independence + drive to become the guide he never had. (Stories #1, #2, #3, #5, #10, #13)
2. Starting Over from Zero - Rebuilt from nothing 3+ times. Pattern: assess -> package -> sell -> learn. (Stories #1, #5, #11, #12, #16, #17)
3. Learning as Survival Strategy - Crisis reflex = learn, not rest. Knowledge acquisition as first step out. (Stories #4, #9, #10, #11, #13, #18)
4. The Price of Ego and the Gift of Humility - Humiliation as recalibration. Strongest growth after deepest humbling. (Stories #3, #5, #12, #15, #20)
5. Protecting the Next Generation - Driven to give his children what he didn't have. (Stories #2, #5, #7, #16, #19, #20)

## 3. VALUES (Hierarchy)

1. Integrity - "Clarity is the highest form of respect."
2. Self-Reliance - "Nobody is coming to save you. So move."
3. Family - "My kids don't need a father who's always catching up."
4. Generosity - "When you've been to the top of the tower, buy someone else's ride up."
5. Continuous Growth - "Your trophies can become the walls of your cage."

## 4. DECISION-MAKING PATTERNS

1. Intuition First, Logic Second - Feel -> Act -> Analyze
2. Speed Over Perfection - 80% ready = GO
3. "Jakos To Bedzie" + Action - Believe -> Declare -> Move -> Adjust
4. Pain as Decision Catalyst - Every pivot came from hitting bottom
5. Against-the-Grain Default - If everyone says don't -> seriously consider doing it

## 5. UNIQUE LANGUAGE MARKERS

Phrases: "Jakos to bedzie", "Po trupach do celu", "Taniec na zyletce", "Nie zatrzymuj sie", "Ziarno sukcesu", "Umysl scisly, dusza artysty"
Speech patterns: Starts with sensory details, builds to lesson organically, uses specific numbers (37 faxes, 140zl, 200K), self-corrects mid-story
Words to AVOID: "Unlock your potential", "Game-changer", "Leverage", "Synergy", "Disrupt", "Thought leader", "Crush it"

## 6. NATURAL METAPHORS

Dance/Choreography: "Dance on a razor blade", "Choreography is architecture", "A formation is a distributed system"
Building/Construction: "Built from whatever's lying around", "Package what you have and sell it", "Three legs: money, health, love"
Nature/Growth: "Seed of success inside every failure", "Grew tomatoes from seed", "Trophies become walls of your cage"
Survival/Journey: "Walking through hell - don't stop", "The donkey who wouldn't fall", "Fell on all four paws"

## 7. THE ONE-LINER

> "Engineer's mind. Artist's soul. Built from scratch - three times."

## 8. CONTENT CREATION RULES

1. First person always
2. Start with a moment, not a lesson
3. Short sentences. Punchy. Then one longer for depth.
4. Numbers are anchors (37 faxes, 140zl, 200K)
5. Polish warmth in English prose
6. Vulnerability allowed. Self-pity not.
7. Dance metaphors natural, never forced
8. End with forward motion
9. No guru jargon
10. Reader thinks "this guy is real" - not "this guy is impressive"
$vdna$, 1, 'tomasz', NOW())
ON CONFLICT (brand_id, config_key) DO UPDATE
  SET config_value = EXCLUDED.config_value, version = brand_config.version + 1,
      updated_by = 'tomasz', updated_at = NOW();

-- Mirror: strona Notion Voice Bible wchodzi do page_map syncu brand_config
UPDATE sync_registry
SET config = jsonb_set(COALESCE(config, '{}'::jsonb), '{page_map,AGS:voice_dna_core}',
                       '"331c00c90b9381afa511fa8c9ae3658c"'::jsonb)
WHERE table_name = 'brand_config';

-- Kontrola
SELECT 'voice_dna_core' AS co, version::text AS v, length(config_value)::text AS len, md5(config_value)
FROM brand_config WHERE brand_id='AGS' AND config_key='voice_dna_core';
SELECT config->'page_map'->>'AGS:voice_dna_core' AS mirror_cel FROM sync_registry WHERE table_name='brand_config';
COMMIT;
