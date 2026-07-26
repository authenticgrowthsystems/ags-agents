# RAPORT DO MANAGERA - Voice Bible v2.2 (25/07/2026)

## Jednym zdaniem

Voice Bible v2.2 gotowa do wdrozenia: sekcja 23 (test szatni) wpieta w kod, SQL wgrania
tresci przygotowany, AP-309 ustanowiony - zostaje jedna rzecz do rozstrzygniecia sonda:
numer wersji, bo db/022 mogla juz zajac version 4.

## Co zrobione (kod + SQL, commit b2365dc na sb-work)

**Sekcja 23 TEST SZATNI - nowa robota kodowa.** `compliance.test_szatni` (LLM Haiku)
przepisuje kalki z angielskiego na polski MOWIONY wg 4 anty-wzorcow i 3 pro-wzorcow z sekcji
23, ze wzorcem canonical Tomasza. To wezsza warstwa niz `polish_pl`: lapie zdania POPRAWNE,
ktore brzmia jak slajd. HARD dla marek PL (w `enforce`, TNM/RDC) i dla KAZDEGO gotowca
sprzedazowego PL (w `sales._draft_outreach`). Origin trzymam w kodzie: korekta na mailu do
Dudzika.

**Sekcje 14 i 20 juz byly** (nie duplikuje): abstract-tech (sekcja 14) zyje jako
`sales._ZAKAZANE_PRODUKTOWE` + auto-odrzut od pkt 3 paczki (babfe03); interpunkcja PL
(sekcja 20) jako `compliance.pl_comma_flags` od pkt 8. Zamiast prompta LLM zrobilem
interpunkcje deterministycznie (tansze, pewniejsze) - flaga w karcie, nie block, zgodnie
z zakresem sekcji 20 (soft).

**AP-309 grep loaderow (Twoj warunek).** Trzy miejsca czytaja voice_bible: `brand.voice_block`
(glowne, wszyscy generujacy), `conversation` (dyskusja CM), `sales` (outreach). WSZYSTKIE przez
`load_brand -> brand['voice_bible']` PELNE, zaden nie tnie po naprawie 24/07. Wiec jedna zmiana
w brand_config dociera do wszystkich - nie ma ukrytego loadera z hardkodem. `voice_block` NIE
ruszony, zostaje bajtowo staly (Twoj drugi warunek - prompt-cache trafia). AP-309 zapisany
w library + docs/anti-patterns.

**SQL db/032** wgrywa pelna tresc v2.2 (sekcje 1-23, instrukcja deploy uciete), history z md5,
guard idempotentny (pomija gdy tresc juz ma 'SEKCJA 23'), dollar-quote.

## Jedno do rozstrzygniecia PRZED wdrozeniem: numer wersji

Prosisz o bump do 4, zakladajac v2.1=3. Ale **db/022 to STARA v2.2 (12/07, inna tresc)**. Jesli
zostala kiedys wdrozona, baza ma juz version 4, a nowa v2.2 idzie na 5. SQL bumpuje `version+1`
od AKTUALNEJ (nie hardkod 4), wiec zrobi poprawnie tak czy inaczej - ale numer koncowy zalezy
od stanu. Sonda przed psql rozstrzyga (jest w komendach dla Tomasza). Dam znac, czy wyszlo 4,
czy 5.

## Krok 3 sekwencji (agent_prompts) - uwaga

Compliance NIE zyje w `agent_prompts` (grep: kod tej tabeli nie czyta) - zyje w `compliance.py`.
`agent_prompts` to rejestr. Realny krok 3 (ABSTRACT_TECH + PL_INTERPUNCTION + TEST_SZATNI
w bibliotece compliance) jest wykonany W KODZIE. Jesli chcesz wpisu rejestrowego do
agent_prompts dla audytu, dopisze - ale to nie zmienia zachowania.

## Cutover

Sekwencja: sonda wersji -> push -> psql db/032 -> rebuild cm-agent -> kontrola (version + sekcja
23 obecna) -> tap-testy 6 przypadkow (sekcja 23 gotowiec-kalka, sekcja 14 abstract-tech, sekcja
20 przecinki, re-intro, cold email, Tryb A). Notion mirror: voice_bible jest wierszem
brand_config, wiec sync worker zmirror sam po zmianie (registry brand_config enabled).
CM dostanie v2.2 przy najblizszym request (cache invalidation przez LISTEN/NOTIFY).
