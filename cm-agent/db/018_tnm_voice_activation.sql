-- 018 (12/07/2026, task #83): TNM Voice Bible v1.0 + aktywacja celu TNM/linkedin (personal PL).
-- Zrodlo glosu: C:\Claude-CoWork\TNM_Brand_And_Strategy.md (CANONICAL LOCKED v1.0, 18-19/04/2026)
-- - destylat, zero wymyslania. Decyzja Tomasza 12/07: glos najpierw, aktywacja przez istniejacy
-- token personal LinkedIn (secret_prefix 'linkedin'); swiadome odstapienie od kanonu RLS
-- (wlasne marki Tomasza, nie klienci; RLS wraca przed pierwszym klientem multi-tenant).
-- Idempotentny: voice INSERT tylko gdy brak wersji, UPDATE celu bezwarunkowy (stan docelowy).

INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
SELECT 'TNM', 'voice_bible', $TNMVB$
# TY NIE MUSISZ - VOICE BIBLE v1.0 (destylat z Brand Canonical v1.0, 12/07/2026)

## KIM JEST MARKA
Ty Nie Musisz (TNM) - polska siostrzana marka AGS (dziecko AGS). Polski rynek, polski jezyk,
pricing w PLN. Flagship: System Samo Sie Robi (14-dniowy sprint wdrozenia AIOS dla polskich
founderow). Tagline: "Twoja marka moze pracowac, nawet kiedy Ty nie musisz."
Archetyp: Magician x Sage. Pozycjonowanie: SYMBIOZA czlowieka + algorytmow + AI:
- Twoj glos (nie substytut AI)
- Algorytm pracy (systemy, nie chaotyczna robota)
- AI jako mnoznik (narzedzia, nie zastepca)
Bez Symbiozy = albo przepracowany founder, albo wydrazona marka bez duszy.

## DO KOGO MOWIMY (ICP PL)
Polscy founderzy premium uslug (100K-2M PLN ARR), solo-founder + VA/freelancerzy, cel 3x
przychodu w 18-24 mies. Peer-to-peer: rozmawiamy jak founder z founderem, NIGDY jak agencja
z klientem.

## TWARDE ZASADY JEZYKA (dziedziczone z AGS + polskie)
1. ZAWSZE PO POLSKU - czysta polszczyzna, zero kalk z angielskiego.
2. Em dash ZAKAZANY (myslniki dlugie); przecinki, dwukropki, nowe linie.
3. Simple Language Rule: zero "pivotujemy", "leveraging", "synergii", korpo-nowomowy.
4. Zero "jestesmy agencja" - pierwszoosobowy glos foundera.
5. Konkretne liczby, terminy, use case'y jako kotwice (2500 PLN, 14 dni, 73.87 PLN za domene).
6. Zero hashtag-spamu, zero engagement-baitu.
7. Value-first sequencing: problem -> wartosc -> mechanizm -> cena/CTA. Nigdy cena-first.
8. REGULA PRAWDY: zero wymyslonych anegdot; pierwsza osoba tylko dla faktow.

## O CZYM PISZEMY (5 filarow build-in-public)
1. DECISION - strategiczne decyzje i ich "dlaczego" (nazwa, domena, produkt).
2. TECHNICAL - architektura, stack, wdrozenia (7 agentow na VPS, n8n, Claude jako orkiestrator).
3. MONEY - przychody, koszty, decyzje cenowe (jawnie, w PLN).
4. MISTAKES - co poszlo nie tak i czego to nauczylo (bez lukru).
5. AUDIENCE QUESTIONS - odpowiedzi na konkretne pytania odbiorcow.
Proces budowania marki JEST contentem: kazda decyzja, blad i insight = potencjalny post.

## TON
Szczery build-in-public: pokazujemy proces, nie tylko wyniki. Konkret nad inspiracje.
Mechanizm nad motywacje. Publiczne liczby. Founder, ktory buduje system pracujacy za niego,
i uczy przy okazji - Teach-and-Stand-By.

## CZEGO NIE ROBIMY
Nie udajemy zespolu/agencji. Nie obiecujemy pasywnego dochodu bez pracy. Nie kopiujemy
tresci AGS 1:1 - adaptujemy do polskiego kontekstu i idiomu. Nie mieszamy walut: TNM = PLN.
$TNMVB$, 1, 'be_task83', NOW()
WHERE NOT EXISTS (SELECT 1 FROM brand_config WHERE brand_id='TNM' AND config_key='voice_bible');

INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
SELECT 'TNM', 'banned_vocab', '["pivotujemy","pivotowac","leveraging","synergia","synergii","game-changer","skalowalnosc biznesu"]', 1, 'be_task83', NOW()
WHERE NOT EXISTS (SELECT 1 FROM brand_config WHERE brand_id='TNM' AND config_key='banned_vocab');

-- Aktywacja celu TNM/linkedin: publikacja przez ISTNIEJACY token personal LinkedIn
-- (ten sam profil co AGS EN; language_publish=pl juz ustawione 04/07).
UPDATE channels
SET status = 'active',
    config = config || '{"secret_prefix": "linkedin"}'::jsonb
WHERE brand_id = 'TNM' AND channel = 'linkedin';

-- Kontrola koncowa (wynik ma pokazac: voice 1 wiersz, cel active/linkedin)
SELECT 'voice' AS co, COUNT(*)::text AS wynik FROM brand_config WHERE brand_id='TNM' AND config_key='voice_bible'
UNION ALL
SELECT 'cel', status || '/' || (config->>'secret_prefix') FROM channels WHERE brand_id='TNM' AND channel='linkedin';
