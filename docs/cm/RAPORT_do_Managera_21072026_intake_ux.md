# RAPORT do Managera - Build INTAKE-UX subagentow (21/07/2026, BE-INTAKE-UX)

Brief: docs/briefs/BRIEF_INTAKE_UX_21072026.md. Galaz: build/intake-ux
(od claude/silly-blackwell-dfc32d 68d96d2). Zero deployu, zero n8n, zero DDL -
wszystko miesci sie w istniejacych trasach dec:/cmt: i istniejacym schemacie.

## Co zbudowane (4 wady z zywej sesji 21/07 ze zrzutow Djordje Klikovac / Dan Martell)

### B1 PAMIEC WATKU SUBAGENTA (najwazniejsze)
Przyczyna wady znaleziona w kodzie: trasy DETERMINISTYCZNE subagenta (wrzutka
zrzutu, kolejka, raport, "co wisi") odpowiadaly i ROBILY RETURN przed
_save_history - wymiana nie trafiala do historii watku. Dlatego subagent sam
strescil DM, a 3 wiadomosci pozniej "nie mial kontekstu".
Fix (jeden kontrakt, nie fork): pomocnik `_sub_record` dopisuje wymiane do TEJ
SAMEJ historii co sciezka LLM (`_load_history`/`_save_history`, histories per
agent). Zapisuja sie: karta intencji (z tym co subagent ZOBACZYL na zrzutach),
paragony wykonania intencji, kolejka/raport/co-wisi. System prompt dostal
twarda zasade: SPRAWDZ historie zanim poprosisz o powtorzenie.
Do tego nowe narzedzie `subagent_reply_dm` - "odpowiedz na ten DM" siega po
ostatnie zrzuty watku samo, zamiast prosic o ponowne wklejenie.

### B2 MENU INTENCJI PO WRZUTCE
Wrzutka zrzutu/albumu NIE odpala juz od razu floodu propozycji. Nowy przeplyw:
`_screen_shots` (wizja-KLASYFIKACJA: osoby, post/DM/profil, propozycja akcji)
-> JEDNA karta "CO WIDZE + PROPONUJE" z guzikami intencji przez decisions.ask,
typ **intent_menu** (wzorzec dec:<id>:<key> - zadnego trzeciego frameworku):
[Skomentuj] [Odpowiedz na DM] [Poznaj osobe (intake)] [Wszystko po kolei]
[Tylko zapisz]. Guziki pokazuja tylko wykryte mozliwosci; rekomendacja ⭐
pierwsza. Tap -> `apply_intent_menu`: wykonanie SEKWENCYJNE, kazdy watek
domkniety paragonem "✅ Watek ... domkniety", po ostatnim "co dalej?".
Pojedynczy wybor przy pozostalych intencjach = karta z POZOSTALYMI opcjami
(wybor kilku pozycji = kolejne tapniecia, zero rownoleglego floodu).
KIERUNEK PRODUKTOWY zapisany: watek intencji = OBIEKT w agent_decisions
(context: insp_ids/contact_id/screening/done_keys) - Slack/webapp wyswietla te
same obiekty inaczej (docs/komponenty/rozmowa-cm.md).
Odpowiedzi na DM jada TYM SAMYM torem co komentarze (_send_author_proposal
kind='dm', marker [DM] w notes, gotowiec "ODPOWIEDZ NA DM DO WYSLANIA",
cmt:done podnosi stadium relacji do 'dm' zamiast 'commented').
Jawne narzedzie suggest_comment_from_image w rozmowie = bez menu (stara
sciezka) - menu dotyczy wrzutek.

### B3 DEDUP WRZUTEK PER OSOBA
Trzy warstwy (dowod wady: Djordje 3x karta "Nowa osoba" + decyzje #6 i #7):
1. `crm.clean_author`: 'Djordje Klikovac • 2nd (He/Him) 🔹' -> 'Djordje
   Klikovac' PRZED dopasowaniem i zapisem stuba (test: 5 wariantow -> 1 osoba);
   find_contact dopasowuje tez po nazwie oczyszczonej.
2. Otwarta karta intent_menu tej osoby <24h -> kolejne zrzuty DOKLEJAJA
   insp_ids do jej kontekstu ("doklejone do otwartego watku"), zero 2. karty.
3. Decyzja crm_tier: JEDNA per osoba w 24h (pending albo swiezo rozstrzygnieta
   = nota zamiast drugiego pytania); karta "Nowa osoba/dam zrzut profilu"
   max 1/24h per kontakt (brand_config crm_intake_offered).

### B4 FORMATOWANIE
JEDNO miejsce wysylki: `_reply` -> `_send_rendered` -> `_md_to_html`
(**pogrubienie** -> <b>, ### naglowek -> <b>, `kod` -> <code>, parse_mode
HTML). Tekst BEZ znacznikow idzie plain (zero ryzyka na '<' i '&'); blad
renderowania = fallback plain (wiadomosc zawsze dochodzi). Czyste wklejki
gotowcow ida poza _reply i zostaja doslowne.

## Bonus: naprawiony zywy blad
Guzik "🔄 Inny kat" (cmt:angle) NIE dzialal od 20/07: galaz importowala
_language_publish bez TRUTH_GUARD -> NameError polykany przez except ->
zawsze "Nie wyszla regeneracja". Import naprawiony; regeneracja DM dostaje
tez wlasciwy prompt (wiadomosc, nie post).

## Weryfikacja
- py_compile: conversation.py, crm.py, decisions.py, engagement.py - PASS.
- Test jednostkowy _md_to_html: **bold**/###/backtick -> HTML, escape a<b i
  R&D, tekst bez znacznikow -> None (plain). PASS.
- Test jednostkowy clean_author: 5 wariantow wyswietlania -> jedna nazwa. PASS.
- Dokumentacja W TYM SAMYM commicie: rozmowa-cm.md + engagement-crm.md.

## Wdrozenie (BE-INTEGRATOR / Tomasz)
Zero DDL, zero patcha n8n. Merge build/intake-ux -> claude/silly-blackwell-dfc32d
-> rebuild cm-agent -> tap-testy DoD:
a) streszczenie DM -> 3 wiadomosci dalej "odpowiedz na ten DM" bez proszenia
   o powtorzenie; b) album 2 zrzutow -> JEDNA karta intencji; wybor 2 pozycji
   (kolejne tapniecia) -> 2 paragony -> "co dalej"; c) ten sam profil 2x ->
   zero drugiej karty/decyzji; d) pogrubienie bez gwiazdek.

## Iteracja po tap-testach z Tomaszem (21/07 wieczor)

Testy d (formatowanie) i b (album -> jedna karta -> sekwencja -> "co dalej") PASS na zywo
(Neil Patel, decyzje #8-#10, intake + crm_tier Competitor). Dwie uwagi Tomasza wdrozone
od reki:
1. **JEDNO zatwierdzenie**: guzik [✅ Wkleilem]/[✅ Wyslalem] (cmt:sent) domyka caly cykl
   jednym tapnieciem (sent + stadium CRM) - koniec dwustopniowego Zatwierdz -> gotowiec ->
   Wkleilem. Stary tor cmt:ok/done zostaje jako legacy dla kart sprzed zmiany; przypomnienie
   24h (stale_comment) dalej lapie niedomkniete propozycje.
2. **Dwujezycznosc + przejrzystosc celu**: naglowek propozycji mowi "🎯 brand/kanal •
   publikacja: EN/PL"; przy kanale nie-PL pod wklejka idzie "🇵🇱 Kontrola po polsku"
   (translate_text, haiku) - Tomasz czyta PL, publikuje native, wklejka zostaje czysta.
   n8n bez zmian (galezie cmt:/dec: routuja po prefiksie - dowod: done/skip weszly 20/07
   bez patcha, dec:intent_menu dzialalo dzis na zywo).

## Ryzyka / obserwacje do backlogu
- Screening = +1 wywolanie wizji (sonnet) per wrzutka - celowy koszt za trafna
  akcje; gdy urosnie, kandydat na haiku.
- Stare brudne stuby contacts sprzed 21/07 nie scala sie same - przy dublu
  scalic recznie SQL-em.
- Telegram u SPRZEDAWCY dalej renderuje surowe ** (sales.py poza zakresem
  briefu - "NIE DOTYKASZ"; ta sama poprawka to 1 linia w sales przy nastepnym
  buildzie: wysylka przez conversation._send_rendered).
