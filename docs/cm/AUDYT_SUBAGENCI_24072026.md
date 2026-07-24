# AUDYT: dlaczego Tomasz nie rozmawia z subagentami X i LinkedIn (24/07/2026)

Zgloszenie Tomasza 24/07: **"zauwazylem ze wcale nie gadam z subagentami X oraz LinkedIn"**.
Audyt czesc 1: DOKUMENTACJA + KOD (bez dostepu do bazy). Czesc 2 (sonda w bazie) wymaga
jednej komendy Tomasza - SQL na koncu pliku.

## Wniosek w jednym zdaniu

Rozmowa z subagentem jest ZBUDOWANA i dziala, ale w codziennym rytmie NIE MA DO NIEJ WEJSCIA:
wszystko, co subagent produkuje, dociera do Tomasza jako **anonimowa karta** (bot #1, bez
badge'a) albo jako **cichy strumien** (bot #2), a sam subagent nigdy nie odzywa sie pierwszy.
Zeby z nim porozmawiac, trzeba samemu pamietac o `/agents`, przelaczyc sie i zaczac.

## Co jest zbudowane (stan faktyczny z kodu)

- `conversation._subagent_handle` - petla agentowa do 5 krokow, 11 narzedzi, pamiec watku
  per agent (16 tur, TTL 30 min), zasady konta z `channels.config.rules`, badge "kto mowi".
- Przelacznik `/agents` ustawia `user_agent_state.active_agent` = `subagent:<brand>:<channel>`.
  Po przelaczeniu KAZDA wiadomosc idzie do tego subagenta, az do kolejnego przelaczenia.
- Trasy deterministyczne subagenta: `kolejka`, `raport`, `co wisi`, wrzutka zrzutu (karta
  intencji), edycja pozycji, reguly konta.

To znaczy: mozliwosc rozmowy nie jest problemem. Problemem jest OKAZJA do niej.

## Cztery znalezione powody (kazdy z miejscem w kodzie)

**1. Odprawa poranna jest wylaczona przez domyslny tryb pracy.**
`proactive.morning_nudge` (jedyna rzecz, ktora sama zaczepia Tomasza rano) zaczyna sie od
`if _work_mode() not in ("semi", "auto"): return`, a `_work_mode()` czyta `brand_config
cm_work_mode` z domyslna wartoscia **`supervised`**. Jesli nikt tego klucza nie ustawil,
odprawa nie odpala sie ANI RAZU. To pierwsza rzecz do sprawdzenia sonda (SQL nizej).

**2. Nawet gdy odprawa dziala, mowi glosem CM, nie kanalu.**
Tresc zaczyna sie od "☕ Odprawa poranna CM" i podsumowuje karty, szkice i plan. Subagent X
ani LinkedIn nie ma w tym swojego zdania: ile jego postow poszlo, co zarezonowalo, czego mu
brakuje.

**3. Potrzeby subagenta ida na bota LOGOWEGO (#2), ktory z definicji nie wybudza.**
`proactive.handle_agent_requests` konczy sie `logbot.send("📌 SUBAGENT[<kanal>] POTRZEBUJE...")`,
a `logbot` wysyla domyslnie z `disable_notification` (kanon 24/07: strumien do czytania, nie
do wybudzania). Prosba subagenta o dane albo dostep laduje wiec w kanale, do ktorego zaglada
sie rzadko - i nigdy nie staje sie rozmowa.

**4. Raporty dzienne i tygodniowe tez ida na bota #2.**
`reports` wola `logbot.send(text)`. Efekt uboczny: caly dorobek pracy subagentow (co wyszlo,
z jakimi metrykami) omija glowny czat, w ktorym Tomasz faktycznie rozmawia.

Dodatkowo: karty przegladu, przypomnienia i propozycje z luk kadencji CELOWO nie maja badge'a
(kanon 24/07: badge = mowi agent, brak badge = system). To dobra zasada, ale w praktyce oznacza,
ze 100% tego, co subagent robi dla Tomasza, dociera bez twarzy.

## CZESC 2: SONDA W BAZIE (24/07 ~20:50) - co pokazaly dane

**Punkt 1 powyzej jest BLEDNY i zostaje jako slad rozumowania.** `cm_work_mode` = **semi**,
wiec odprawa poranna JEST wlaczona. Zalozylem wartosc domyslna z kodu zamiast sprawdzic
zywa - dokladnie ten blad, przed ktorym ostrzega kanon DOCS-FIRST (diagnoza z dowodu, nie
z hipotezy). Powody 2, 3 i 4 zostaja w mocy.

Co pokazala sonda NAPRAWDE:

**A. Aktywny agent to JEDEN SLOT na czat, i trzyma go Sprzedawca.**
`user_agent_state`: jeden wiersz, `active_agent = subagent:AGS:sprzedaz`, ostatnia zmiana
24/07 18:53. Skoro slot jest jeden, to rozmowa z subagentem X wymaga PORZUCENIA Sprzedawcy
i pozniejszego powrotu. Przy dwoch aktywnych frontach (kampania sprzedazowa + content) wygrywa
ten, ktory akurat pali sie bardziej - i tak subagenci contentu wypadaja z rytmu dnia.
To jest strukturalny powod, mocniejszy niz brak zaproszenia do rozmowy.

**B. Watki rozmow sa PUSTE.**
`fsm_data->'histories'` nie ma ani jednego wpisu (zero wierszy w sondzie), przy 48 wpisach
`CONVERSATION_SUMMARY` w `agent_logs` (ostatni 24/07 19:24) i 48 zadaniach `memory_summary`
w ledgerze. Czyli mechanizm streszczania dziala i CZYSCI watki po TTL 30 min, a trwale
zostaje tylko skrot. Skutek praktyczny: kazda rozmowa z subagentem zaczyna sie zimno,
z podsumowania, a nie z watku. Przy rozmowie raz na kilka dni to znaczy: zawsze od zera.

**C. Subagent nigdy o nic nie poprosil.**
`agent_logs` z typem `CHANNEL_NEED`: **zero wpisow**. Sciezka "subagent zglasza potrzebe
zasobu, CM przekazuje Tomaszowi" istnieje w kodzie od 06/07 i w produkcji nie odpalila sie
ANI RAZU. Albo subagenci nigdy niczego nie potrzebuja (nieprawdopodobne przy braku metryk
LinkedIna i limitach X), albo prompt nie sklania ich do proszenia. To pole do sprawdzenia
osobno.

**D. Rozmowy jednak sa, tylko nie z tymi agentami.**
Ledger `cm_tasks` za 30 dni: `conversation` (CM) 149 wywolan, `subagent_chat` 118,
`sales_chat` 69. Czyli subagenci ROZMAWIALI - tylko rozklad w czasie i per kanal jest
nieznany (ledger nie trzyma identyfikatora agenta). Hipoteza do weryfikacji: 118 wywolan
pochodzi z okresu testow 07-12/07, a nie z ostatniego tygodnia. Sonda rozstrzygajaca
(agent_logs trzyma `agent_id` przy streszczeniach):

```bash
docker exec -i pg_n8n psql -U n8n -d ags_crd -c "SELECT agent_id, COUNT(*) AS streszczen, MAX(created_at) AS ostatnia_rozmowa FROM agent_logs WHERE log_type='CONVERSATION_SUMMARY' GROUP BY agent_id ORDER BY ostatnia_rozmowa DESC;"
```

## Czego audyt NIE rozstrzyga bez bazy

- czy `cm_work_mode` jest ustawiony (a wiec czy odprawa w ogole odpala),
- ile razy Tomasz faktycznie przelaczyl sie na subagenta i kiedy ostatnio,
- czy watki rozmow subagentow (`user_agent_state.fsm_data.histories`) maja jakakolwiek tresc,
- ile wywolan modelu poszlo na rozmowe subagenta w ostatnich 30 dniach (`cm_tasks`).

### Sonda (SSH, read-only, jedna komenda)

```bash
docker exec -i pg_n8n psql -U n8n -d ags_crd <<'SQL'
\echo '--- 1) tryb pracy CM (supervised = odprawa poranna NIE odpala) ---'
SELECT config_key, config_value FROM brand_config
 WHERE brand_id='AGS' AND config_key IN ('cm_work_mode','admin_chat_ids');

\echo '--- 2) aktywny agent per czat + kiedy ostatnio ruszony ---'
SELECT chat_id, active_agent, updated_at FROM user_agent_state ORDER BY updated_at DESC;

\echo '--- 3) czy watki subagentow maja historie (ile tur per agent) ---'
SELECT chat_id, k AS agent, jsonb_array_length(v) AS tur
  FROM user_agent_state, jsonb_each(COALESCE(fsm_data->'histories','{}'::jsonb)) AS e(k,v)
 ORDER BY tur DESC;

\echo '--- 4) wywolania modelu per typ zadania (30 dni) ---'
SELECT task_type, COUNT(*) AS n, ROUND(SUM(cost_usd)::numeric,4) AS usd
  FROM cm_tasks WHERE created_at > NOW() - interval '30 days'
 GROUP BY task_type ORDER BY n DESC;

\echo '--- 5) czy subagenci w ogole o cos prosili ---'
SELECT log_type, COUNT(*) AS n, MAX(created_at) AS ostatnio
  FROM agent_logs WHERE log_type IN ('CHANNEL_NEED','CONVERSATION_SUMMARY')
 GROUP BY log_type;
SQL
```

## Rekomendacja po sondzie (do decyzji Tomasza, NIE wykonane)

Rezim stabilizacji mowi: na subagentach zero nowych funkcji bez decyzji. Dlatego audyt konczy
sie propozycjami, nie kodem. Kolejnosc zmieniona po danych - najpierw to, co usuwa STRUKTURALNA
przeszkode, potem to, co daje zaproszenie do rozmowy:

1. **Adresowanie agenta bez przelaczania slotu** (usuwa przyczyne A). Prefiks w wiadomosci:
   `x: ...`, `li: ...`, `cm: ...` idzie do wskazanego agenta i NIE zmienia aktywnego.
   Sprzedawca zostaje w slocie przez cala kampanie, a content dostaje glos jednym slowem.
   Zmiana w jednym miejscu (route w `conversation.handle`), zero DDL, odwracalna.
2. **Meldunek dnia od KAZDEGO subagenta w glownym czacie, z badge'em** (zamiast albo obok
   cichego raportu na bocie #2): trzy linie - co poszlo, co zarezonowalo, czego potrzebuje,
   plus guzik "Odpisz". To zamienia raport w zaczepke do rozmowy.
3. **Prosba subagenta (CHANNEL_NEED) jako decyzja guzikami w glownym czacie**, nie linia
   w cichym strumieniu. Mechanizm juz jest (`decisions.ask`), brakuje przelaczenia toru.
   Uwaga: najpierw sprawdzic, DLACZEGO ta sciezka nie odpalila sie ani razu (przyczyna C) -
   przelaczanie toru, ktorym nic nie plynie, niczego nie naprawi.
4. **Watek subagenta z dluzszym TTL albo wznawianie ze skrotu** (przyczyna B). Dzis 30 minut
   ciszy kasuje watek, a rozmowa raz na kilka dni zawsze zaczyna sie zimno. Tanszy wariant:
   przy pierwszej wiadomosci do subagenta wstrzykiwac ostatni `CONVERSATION_SUMMARY` jawnie
   ("ostatnio rozmawialismy o...") zamiast pozwalac mu udawac, ze pamieta.

Punkty 1-4 to zmiana INTERFEJSU i PAMIECI, nie mozgu (kanon WARSTWY: interfejs jest wymienny),
wiec sa odwracalne. Zadnego z nich nie robie bez Twojej decyzji.
