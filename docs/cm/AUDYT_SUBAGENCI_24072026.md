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

## Rekomendacja (do decyzji Tomasza, NIE wykonane)

Rezim stabilizacji mowi: na subagentach zero nowych funkcji bez decyzji. Dlatego audyt konczy
sie propozycjami, nie kodem. Kolejnosc wg stosunku wartosci do ryzyka:

1. **Sprawdzic i ustawic `cm_work_mode`** (jesli sonda pokaze `supervised`). Jedna linia SQL,
   zero kodu - i odprawa poranna zaczyna istniec.
2. **Meldunek dnia od KAZDEGO subagenta w glownym czacie, z badge'em** (zamiast albo obok
   cichego raportu na bocie #2): trzy linie - co poszlo, co zarezonowalo, czego potrzebuje.
   To zamienia raport w zaczepke do rozmowy.
3. **Prosba subagenta (CHANNEL_NEED) jako decyzja guzikami w glownym czacie**, nie linia
   w cichym strumieniu. Mechanizm juz jest (`decisions.ask`), brakuje tylko przelaczenia toru.
4. **Guzik "Odpisz subagentowi" pod jego meldunkiem**, ktory ustawia `active_agent` - zeby
   rozmowa zaczynala sie jednym tapnieciem, a nie pamiecia o `/agents`.

Punkty 2-4 to zmiana INTERFEJSU, nie mozgu (kanon WARSTWY: interfejs jest wymienny), wiec sa
odwracalne. Zadnego z nich nie robie bez Twojej decyzji.
