# Komponent: N8N TRANSPORT (HITL, publishery, crony, zasady PUT)

**STATUS GOTOWOSCI: KOMPLETNY** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

n8n = TYLKO TRANSPORT (kanon): odbiera Telegram/webhooki, routuje, strzela
w endpointy agentow i publikuje przez API platform. ZERO logiki biznesowej
w n8n - mozgi mieszkaja w kontenerach Python (cm-agent, ags-researcher).

## Workflowy (stan LIVE)

| Workflow | ID | Rola |
|---|---|---|
| HITL handler | `U5pUZjy2yAhR1sWg` | JEDYNY konsument bota Telegram (~252 wezly). **PISZE do `content_items`** (wezel `Cm Resolve Gate`, z pominieciem cm-agenta) |
| Subagent X Publisher | `G3nEIt5lIkiKemiK` | OAuth1 POST /2/tweets (+ media v2 chunked) |
| Subagent LinkedIn Publisher | `Uv9TvUMI8MRSqCLz` | Bearer POST /v2/ugcPosts; GENERYCZNY per cel (secret_prefix) |
| Scheduler | `x1jJEbcWAe3FnpCa` | co minute: post_queue 'scheduled' -> publish. **PISZE do `content_items`** (wezly `Mark Published` / `Mark Published LI` domykaja material na `published`) |
| CM Reports Cron | `ERweY5vHomrpw1SC` | 08:00 daily / nd 20:00 weekly / nd 20:15 plan |
| Drift check cron | - | 03:00 (sync Notion) |
| Backup | - | 03:30 |
| Researcher - * (5 adapterow) | - | web_search / firecrawl / gemini_dr / openai_dr / manus |
| AGS Lacznik Chat Tools | `yxJUJmZpSUe0tw9K` | MCP serwer narzedzi czatu (stan_gry, wyslij_raport_pracy) + webhooki wariantu B (chat-raport, stan-gry); szczegoly lacznik.md |

## KTO PISZE DO `content_items` (dopisane 03/08/2026, po D-008)

**Pisarzy jest TRZECH, nie jeden.** Ta lista istnieje, bo przy migracji D-008 dwaj z nich
umkneli dwóm niezaleznym odczytom - szukano po WARTOSCI (`dispatching`), a wezel bota
tego slowa w ogole nie zawiera. **Szukaj po nazwie TABELI, nie po wartosci.**

| pisarz | co zapisuje | czy widac go grepem po wartosci |
|---|---|---|
| kontener `cm-agent` (`worker.py`) | caly cykl zycia materialu | tak |
| n8n `AGS Scheduler v1` | `published` po udanej publikacji | tak |
| n8n `AGS HITL Handler v1.0` | `approved` / `rejected` przy tapnieciu guzika | **NIE** |

**Konsekwencja operacyjna:** kazda migracja dotykajaca `content_items` musi uwzglednic
n8n, a nie tylko `docker stop cm-agent`. Procedura wzorcowa: `docs/ops/OKNO_d008_03082026.md`.

**Konsekwencja druga (10/08, D-016): teksty widziane przez czlowieka tez sa TUTAJ, nie w kodzie.**
Wezel `Cm Resolve Gate` odpowiada po tapnieciu guzika stalym napisem "Zatwierdzono. Publikacja
za chwile." - takze wtedy, gdy CM sekunde pozniej melduje slot za dobe. To AP-312 w wydaniu
czasowym i **nie da sie tego naprawic rebuildem kontenera**, bo napis siedzi w definicji
workflow. Szukajac zrodla mylacej wiadomosci w bocie: sprawdz n8n, ZANIM zaczniesz czytac
`cm-agent/app`. Wpis: `docs/ops/DLUG_TECHNICZNY.md` D-016.
Patch: `n8n-workflows/patches/d016-potwierdzenie-bez-obietnicy-11082026.cjs`.

## ⚠️ EKSPORTY W `n8n-workflows/` SA PRZESTARZALE - nie czytaj ich jak stanu systemu

Ustalone 11/08. `x-agent/ags-hitl-handler-v1.json` ma `updatedAt` **2026-06-11**, 143 wezly
i **nie zawiera wezla `Cm Resolve Gate`**, ktory na produkcji obsluguje guziki zatwierdzania.
Napisu "Publikacja za chwile" nie ma NIGDZIE w repozytorium.

**Zasada praktyczna:** eksporty sa migawka z dnia eksportu, nie zrodlem prawdy. Zrodlem prawdy
jest definicja w n8n. Wszystkie skrypty w `patches/` czytaja ZYWA definicje przez API i to jest
powod, dla ktorego dzialaja mimo dryfu - `d016-*` idzie krok dalej i nie szuka wezla nawet
po nazwie, tylko po tresci, bo nazwa tez mogla sie zmienic.

**Re-eksport zywego workflow do repo** (Bash, ze srodowiskiem jak przy patchach):

```bash
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_BASE_URL/api/v1/workflows/U5pUZjy2yAhR1sWg" \
  | python -m json.tool > n8n-workflows/x-agent/ags-hitl-handler-v1.json
```

Identyfikatory pozostalych: Scheduler `x1jJEbcWAe3FnpCa`, Lacznik `yxJUJmZpSUe0tw9K`.
**Eksport ZAWIERA nazwy poswiadczen, ale nie ich wartosci** - sekrety zyja w `app_secrets`
i w credentialach n8n, wiec plik jest bezpieczny do commitu. Przejrzyj diff przed zapisem,
bo `webhookId` zmienia sie przy imporcie i produkuje szum.

**Pulapka wezla `Mark Published`:** ma w JEDNYM zapytaniu wartosci z DWOCH roznych slownikow -
`ci.status` (material) i `q.status IN (...)` (kolejka), obie do 03/08 o tej samej nazwie
`dispatching`. Podmiana "po calym tekscie" zrywa dopasowanie kolejki bez zadnego bledu,
bo SQL zostaje poprawny. Skrypt `n8n-workflows/patches/d008-handed-off-03082026.cjs` robi
to chirurgicznie i sam odmawia, gdy liczby sie nie zgadzaja.

## HITL: struktura routingu

- **Detect Update Type** = router komend i typow update'u. Przepustka komend
  do cm-agenta: /karty /schowek /decyzje /brand* (reszta tekstu idzie torem
  active_agent). Galezie dokumentow: document_xlsx (metryki) i document_text
  (.md/.txt -> /docmsg). Photo route: 3-drozna (subagent/cm/idea).
- **Callbacki** (kazda rodzina = wlasna galaz z guardem sekretu przed Fire):
  `cm:` approve/reject materialu | `ccp:` legacy intake | `matnav:`/`matdec:`
  karty | `cmt:` komentarze | `dec:` decyzje ustrukturyzowane | `crit:`
  eskalacja critical Researchera | `mtier:` korekta modelu | `agsel:` wybor
  agenta (+ setMyCommands per czat) | `idea:`/`synth:` Idea Bot.
- **Parse And Authorize Set** = ALLOWLISTA kluczy `/set` z freetext keys.
  Nowy klucz konfiguracyjny wymaga PATCHA tego wezla (incydent:
  /set cm_dup_threshold odrzucony - klucz nieznany).
- Glos: OpenAI Whisper (multipart); binaryMode=separate na wezlach binarnych.

## Konfiguracja i sekrety

- Sekrety WYLACZNIE z `app_secrets` (Lookup/Get Key wezlami Postgres w locie);
  zero literalow w definicjach; `saveData` OFF na adapterach z kluczami.
- Endpointy cm-agent (FastAPI :8089, guard X-Researcher-Secret): /message
  /matnav /plannav /cmt /decnav /docmsg /metrics/xlsx /wake /request /plan
  /reports/<kind> /health.
- Env do skryptow ops (Bash): `set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)='
  "C:/Claude-CoWork/AGS/ags-agents/.env" | sed 's/\r$//') && set +a && node skrypt.cjs`

## Zasady zmian (TWARDE)

1. Przed patchem: GET zywej definicji z API n8n (kopia w repo moze byc stara)
   + BACKUP JSON (`bk_*.json`).
2. PUT TYLKO z polami `{name, nodes, connections, settings}` (settings
   PRZEFILTROWANE - inne pola wywalaja 400).
3. Po KAZDYM PUT: **deactivate + activate** - PUT zapisuje do DB, ale aktywny
   snapshot webhookow trzyma STARA definicje (project_n8n_reactivate_after_put).
4. Weryfikacja po PUT: GET + sprawdz active=true, liczbe wezlow, parametry
   zmienionych wezlow, binaryMode=separate nietkniety.
5. Patchery i weryfikatory: `C:\Users\Admin\AppData\Local\Temp\ags-media-spike\`
   (hitl-*.cjs z backupami, verify-*.cjs read-only przez temp webhook -
   temp webhook SKASOWAC po uzyciu).
6. HITL jest wspoldzielony przez wszystkie mechanizmy - sesje budowlane bez
   jawnych praw NIE dotykaja n8n (skladanie robi integrator).

## Punkty zaczepienia w kodzie

- Kopie workflowow Researchera: `n8n-workflows/researcher/*.json` (zywa
  definicja NADRZEDNA - najpierw GET).
- Konsumenci endpointow: patrz rozmowa-cm.md, karty-hitl.md, decyzje-nauka.md,
  metryki.md.

## Kanony ktore go dotycza

- n8n = tylko transport; logika w Pythonie.
- Event-driven: kazdy zapis "dla CM" konczy sie POST /wake (poll 30s = tylko
  backstop). TODO: publishery po callbacku jeszcze nie wolaja /wake.
- AP-301: preferuj edycje parametrow ISTNIEJACYCH wezlow nad dokladanie nowych.

## Znane pulapki

- Najczestszy blad operacyjny: PUT bez deactivate+activate - "patch wszedl,
  a zachowanie stare".
- Router komend POLYKAL nowe komendy (/karty) - kazda nowa komenda tekstowa =
  sprawdz Detect Update Type.
- Allowlista /set nie zna nowych kluczy (cm_dup_threshold w backlogu) -
  do czasu patcha strojenie przez SQL na brand_config.
- Stare wezly HITL maja HARDKODY tokena Telegram (rotacja tokena = przejrzec
  wezly, nie tylko app_secrets).
- Telegram getFile limit 20MB; file_id jest trwaly (wystarczy zapisac id).
