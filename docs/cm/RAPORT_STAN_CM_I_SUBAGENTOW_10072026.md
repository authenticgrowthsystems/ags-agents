# RAPORT: stan budowy CM + subagentow X i LinkedIn (10/07/2026)

Na pytanie Tomasza: czy subagenci maja te same funkcje, jak trzymana jest ich pamiec
i kontekst, czy mozna z nimi swobodnie rozmawiac i beda pamietac.
Zrodlo = audyt kodu cm-agent/app (conversation.py 1629 linii, proactive.py, worker.py,
generate.py, slots.py, planner.py), nie pamiec sesji.

## 1. CONTENT MANAGER - stan budowy

CM NIE jest skonczony (kanon: nigdy nie mowimy "gotowy"), ale ma juz duzo wiecej niz
szkielet egzekucyjny:

ZBUDOWANE I LIVE:
- **Rozmowa dwukierunkowa** na Telegramie: model Opus (przelaczalny per zadanie),
  PETLA AGENTOWA do 5 krokow (wynik narzedzia wraca do modelu - CM moze zawolac
  find_similar, dostac wynik i zaproponowac podmiane, nie utyka na liscie).
- **15 narzedzi rozmowy**: propose_material, save_to_schowek, show_archive,
  find_similar_published (pgvector semantyczne), adapt_published, plan_build,
  plan_approve, plan_edit, target_create, target_update, show_review_cards,
  attach_last_photo, add_style_rule, reschedule_material, replace_material.
- **Partner dialogiczny** (standard 07/07): wlasne zdanie + kat, runda doprecyzowania
  przed zapisem, dedup proponuje PODMIANE zamiast listy podobnych.
- **Planowanie**: plan tygodnia (niedziela 20:15 + na zadanie), zarys miesiaca,
  model jednego zatwierdzenia, publikacja awaryjna po 24h milczenia.
- **Sloty**: Tomasz zatwierdza TRESC, CM przydziela KIEDY (okna per cel, kadencja,
  automatyczny slot dla approved bez slotu).
- **Proaktywnosc**: odprawa poranna 09:00, wykrywanie luk kadencji dzis/jutro,
  obsluga wnioskow agent->agent (negocjacje siatki slotow), przypomnienie o metrykach.
- **Raporty**: dzienny 08:00, tygodniowy nd 20:00 (cron n8n -> bot #2).
- **Przeglad materialow**: karty v9 (kompakt/rozwin/dzien/filtry), guziki intake,
  edycja = akceptacja + nauka stylu, Inny kat wiadomoscia.

BRAKUJE (wg kanonu "realny CM"):
- Planowanie 2-miesieczne (dzis: tydzien + zarys miesiaca).
- Pelna glebia nadzoru nad subagentami (dzis: negocjacje + intake propozycji luk).
- Petla nauki z metryk (patrz O5 w SUBAGENT_DUTIES_v1.md).

## 2. SUBAGENCI X i LINKEDIN - czy maja te same funkcje?

**TAK - to jest DOSLOWNIE TEN SAM KOD.** Subagent nie jest osobnym programem per kanal:
istnieje JEDEN generyczny subagent (funkcja _subagent_handle), a "AGS x" i "AGS linkedin"
to ten sam mechanizm uruchomiony z innym (brand, channel) i inna konfiguracja z tabeli
channels. Zero rozjazdu funkcji w rozmowie - obaj maja identyczne 10 narzedzi:

1. subagent_show_post (pelna tresc + kopia PL do przegladu dla kanalu EN)
2. subagent_edit_post (edycja = akceptacja; dwuetapowo 'edytuj #id'; PL->EN tlumaczenie)
3. subagent_remove_post
4. subagent_reschedule_post
5. subagent_set_metrics (reczny wpis metryk)
6. propose_material (zablokowany do WLASNEGO kanalu)
7. escalate_to_cm (sprawy strategiczne agent->agent, antydubel)
8. suggest_comment (cudzy post tekstem -> 3 komentarze comment-first)
9. suggest_comment_from_image (zrzut -> Claude vision -> komentarz per autor -> guziki decyzji)
10. subagent_remember_rule (trwale zasady konta)

Do tego wspolne: raport na zadanie, kolejka na komende, deterministyczna edycja,
log decyzji autonomicznych, pamiec interakcji.

**Roznice sa TYLKO w 3 miejscach (celowe, nie braki):**

a) KONFIGURACJA per cel (tabela channels): okno publikacji (x 13-22, li 13-18 WAW),
   jezyk publikacji, kadencja, zasady konta, voice_note.
b) STRATEGIA (tekst od CM w kontekscie): X = 3-5/dzien; LinkedIn = pn-pt post,
   sob nic, nd ARTYKUL. LinkedIn zna podzial glosow (personal = czlowiek,
   strona = firma).
c) ADAPTERY PUBLIKACJI (poza subagentem, w n8n + generatorze):
   - X: OAuth1 + media v2 chunked, dluga tresc = NITKA (thread), krotkie formy 500-600 zn.
   - LinkedIn: token profilu (do ~02/09), obrazy dzialaja (post z obrazem opublikowany);
     ARTYKUL = gotowiec (API LinkedIn nie publikuje artykulow - wklejka reczna).
   - Ograniczenia zewnetrzne, nie kodu: X odczyt metryk = platny tier (reczny wpis),
     LinkedIn metryki = kolektor gotowy, czeka na App 2 CMA; strony firmowe LI
     czekaja na tokeny (status ready).

Asymetria powierzchni: subagent LinkedIn opiekuje sie 4 powierzchniami (profil +
3 strony ready), subagent X jedna (konto TNM X = przyszlosc). Obaj ZNAJA wszystkie
swoje powierzchnie i statusy (sekcja TWOJE POWIERZCHNIE w kontekscie).

Jedyna funkcjonalna roznica CM vs subagent: **CM ma petle agentowa (5 krokow), subagent
jest single-pass** (narzedzia wykonuja sie raz, wynik nie wraca do modelu) + CM = Opus,
subagent = Sonnet (oba przelaczalne per zadanie przez cm_tier_*). To decyzja kosztowa,
nie przypadek - ale ogranicza "partnerskosc" subagenta w zlozonych watkach.

## 3. PAMIEC I KONTEKST - jak to jest trzymane

**Trzy warstwy:**

### Warstwa 1: historia rozmowy (krotkoterminowa)
- Tabela user_agent_state, pole fsm_data.histories[agent] - OSOBNY watek per agent
  w tym samym czacie (przelaczenie CM -> subagent NIE miesza rozmow).
- Limit: **16 tur** + **TTL 30 minut** - po pol godzinie ciszy historia sie CZYSCI
  (swiadoma decyzja projektowa: stan nie gnije, /cancel zawsze wychodzi).

### Warstwa 2: pamiec trwala (nie wygasa NIGDY)
- **Zasady konta**: 'zapamietaj...' -> subagent_remember_rule -> channels.config.rules
  (max 20) - wstrzykiwane do KAZDEJ rozmowy i do generacji tresci.
- **Reguly stylu**: add_style_rule + nauka z edycji (style_learned).
- **Pamiec interakcji**: engagement_log per konto (komentarze, decyzje ZATWIERDZONE/
  ODRZUCONE) - subagent widzi ostatnie 5 w kazdej rozmowie ("co juz bylo").
- **Archiwum semantyczne**: content_memory (pgvector + embeddingi) - "czy juz o tym
  pisalismy", top performing, adaptacje miedzy kanalami.
- **Schowek** (inspirations), kolejka, publikacje, plan - stan systemu, zawsze aktualny.
- **Ustalenia z CM**: agent_messages - subagent widzi 2 ostatnie odpowiedzi CM.
- **Log decyzji**: agent_logs AUTONOMOUS_DECISION + CHANNEL_NEED.

### Warstwa 3: kontekst wstrzykiwany swiezo przy KAZDEJ wiadomosci
- CM: stan operacyjny, cele+konfiguracja, kolejka (60 pozycji), propozycja planu,
  ostatnie publikacje, Voice Bible (cache).
- Subagent: konfiguracja celu, WSZYSTKIE powierzchnie rodziny, strategia od CM,
  zasady konta, ostatnie interakcje, kolejka (15), publikacje (5), ustalenia z CM.

## 4. ODPOWIEDZ WPROST: "czy moge swobodnie rozmawiac i beda pamietac?"

**Swobodna rozmowa: TAK** - z CM i z kazdym subagentem, pelny dialog z narzedziami,
osobne watki per agent.

**Pamiec: TAK, ale z jedna granica.** W ramach rozmowy (do 30 min przerwy, 16 tur)
pamietaja wszystko. Po 30 minutach ciszy WATEK LUZNEJ ROZMOWY znika - zostaje tylko to,
co zapisano trwale: zasady konta, reguly stylu, materialy, decyzje, interakcje,
archiwum. Czyli: "zapamietaj, ze zadnych nitek do 1000 followers" - zapamieta NA ZAWSZE.
Ale "fajnie wczoraj gadalismy o tym pomysle" bez zapisu do schowka - tego juz nie ma.

**Rekomendacja Managera (kandydat do sprintu):** dlugoterminowa pamiec rozmow -
przy wygasaniu TTL zapisywac SKROT watku (podsumowanie 3-5 zdan) do trwalej pamieci
agenta i wstrzykiwac ostatnie skroty do kontekstu. Wtedy "pamietasz o czym wczoraj
rozmawialismy" zadziala naturalnie. Drugi kandydat: petla agentowa dla subagentow
(dzis single-pass) - pelny partner na wzor CM.
