# RAPORT: LACZNIK ETAP 2 zbudowany (BE-LACZNIK-E2, 22/07/2026 wieczor)

Brief: docs/briefs/BRIEF_LACZNIK_ETAP2_22072026.md. Galaz: `build/lacznik-e2`
(od origin/claude/silly-blackwell-dfc32d 895be1e). ZERO DDL. HITL i Scheduler
NIETKNIETE (nowy osobny workflow). Maszyneria publikacji nietknieta (rezim
stabilizacji biegnie rownolegle).

## 1. Co zbudowane (i JUZ zweryfikowane sondami)

1. **Workflow n8n "AGS Lacznik Chat Tools"** - id `yxJUJmZpSUe0tw9K`, LIVE
   (utworzony i aktywowany przez API 22/07 ~18:20). W srodku:
   - MCP Server Trigger (typeVersion 2 = streamable HTTP) ze sciezka-sekretem,
   - narzedzie `stan_gry(scope)` -> GET http://cm-agent:8089/lacznik/stan,
   - narzedzie `wyslij_raport_pracy(kanal, raport_md)` -> POST /lacznik/raport,
   - wariant B: webhook POST /webhook/chat-raport + GET /webhook/stan-gry
     (czysty przelot; sekret podaje wolajacy, walidacja w cm-agent).
   DOWOD: sonda MCP initialize -> tools/list = 200, oba narzedzia widoczne.
   DOWOD wariantu B: GET /webhook/stan-gry -> czyste {"detail":"Not Found"}
   od cm-agenta (endpoint wejdzie z rebuildem) = rurociag dziala.
   Wersja n8n: potwierdzona EMPIRYCZNIE (mcpTrigger v2 dziala; przy typeVersion 1
   trigger wystawial tylko SSE na <url>/sse - udokumentowane w lacznik.md).
2. **Cienkie endpointy cm-agent** (`cm-agent/app/worker.py`, py_compile OK):
   - `GET /lacznik/stan?scope=` -> reports.kontekst_text (sync, zero LLM),
   - `POST /lacznik/raport {kanal, raport}` -> engagement.apply_work_report
     (ISTNIEJACY parser, idempotencja) -> potwierdzenie z licznikami wraca
     w odpowiedzi HTTP **+ kopia do Telegrama** + wake petli,
   - guard `_lacznik_guard`: sekret `lacznik_e2_secret` czytany z app_secrets
     W BAZIE per zadanie (rotacja bez rebuildu; brak klucza = 401 dla wszystkich).
3. **Masterprompty czatowe v3** (pelne nowe pliki, docs/product/masterprompty-czat/):
   `MASTERPROMPT_CZAT_X_v3.md` + `MASTERPROMPT_CZAT_LINKEDIN_AGS_v3.md` -
   rytual startu = narzedzie stan_gry, rytual konca = wyslij_raport_pracy,
   fallback = stary rytual (konektor Notion + plik .md). Format raportu BEZ zmian.
4. **README podpiecia** (masterprompty-czat/README.md): instrukcja krok po kroku
   claude.ai -> Settings -> Connectors -> Add custom connector + wariant B.
5. **Schemat OpenAPI wariantu B** (OPENAPI_LACZNIK_WARIANT_B.yaml) dla Custom GPT.
6. Dokumentacja w tym samym commicie: lacznik.md (sekcja Etap 2 + pulapki),
   n8n-transport.md (wiersz workflowu), SYSTEM_DATAFLOW.md (indeks + przeplyw),
   RESUME masterprompt + STATUS w briefie.

JAWNE ODSTEPSTWO (udokumentowane w lacznik.md): sekret stoi literalem w tym JEDNYM
dedykowanym workflow (path triggera + naglowki narzedzi), bo wezly-narzedzia MCP
wykonuja sie pojedynczo i nie moga czytac app_secrets wezlem Postgres jak HITL.
Zrodlo prawdy = app_secrets; saveDataSuccessExecution=none.

## 2. Co zostalo u Tomasza (kolejnosc; kazdy krok = pelna komenda)

KROK 1 - push galezi (PowerShell):
```
git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sprzedaz-research-build-afac01" push origin build/lacznik-e2
```

KROK 2 - merge do galezi serwera + push (PowerShell, worktree sb-work):
```
git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" pull --ff-only
git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" merge origin/build/lacznik-e2 -m "Merge Lacznik Etap 2 (narzedzia MCP czatu)"
git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" push origin claude/silly-blackwell-dfc32d
```

KROK 3 - sekret do app_secrets (SSH na Mikrus, jedna linia):
```
docker exec -i pg_n8n psql -U n8n -d ags_crd -c "INSERT INTO app_secrets (key, value) VALUES ('lacznik_e2_secret', '<SEKRET-Z-CZATU-BUILDA>') ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value;"
```

KROK 4 - rebuild cm-agent (SSH, standardowy szablon; ZERO DDL w tym buildzie):
```
cd ~/ags-agents && git pull --ff-only && cd cm-agent && docker build -t cm-agent:latest . && docker stop cm-agent && docker rm cm-agent && docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:latest && sleep 5 && curl -fsS http://localhost:8089/health; echo
```

KROK 5 - konektor w claude.ai (instrukcja krok po kroku:
docs/product/masterprompty-czat/README.md). URL konektora:
```
https://ivy147-20147.mikrus.cloud/mcp/lacznik-<SEKRET-Z-CZATU-BUILDA>
```

KROK 6 - masterprompt v3 do projektow czatowych (podmiana pliku w projekcie X
i LinkedIn na wersje v3).

## 3. Tap-testy DoD (z Tomaszem, po krokach 1-6)

a) Sesja czatowa Claude z konektorem: "pokaz stan gry x" -> agent wola stan_gry
   i streszcza stan zgodny z baza (sonda read-only potwierdza zrodlo).
b) Koniec sesji JEDNYM poleceniem "wyslij raport" -> narzedzie -> potwierdzenie
   z licznikami wraca DO CZATU + wpisy w engagement_log + Telegram dostaje kopie.
c) Podwojne wyslanie tego samego raportu -> "pominiete duplikaty" (idempotencja).
d) Wylaczony konektor -> masterprompt v3 sam schodzi na fallback (Notion + plik).

Szybka sonda techniczna PRZED tap-testami (po kroku 4, z lokalnej maszyny):
```
curl -s "https://ivy147-20147.mikrus.cloud/webhook/stan-gry?secret=<SEKRET-Z-CZATU-BUILDA>&scope=x"
```
Oczekiwane: {"ok":true,"stan":"# STAN GRY AGS (x) ..."}. Zly sekret -> 401.

## 4. Pliki builda

- n8n-workflows/lacznik-chat-tools-create-22072026.cjs (skrypt, idempotentny,
  rotacja sekretu przez env LACZNIK_E2_SECRET)
- n8n-workflows/lacznik-chat-tools.json (kopia definicji BEZ sekretu)
- cm-agent/app/worker.py (endpointy /lacznik/*)
- docs/product/masterprompty-czat/{MASTERPROMPT_CZAT_X_v3.md,
  MASTERPROMPT_CZAT_LINKEDIN_AGS_v3.md, README.md, OPENAPI_LACZNIK_WARIANT_B.yaml}
- docs/komponenty/{lacznik.md, n8n-transport.md}, docs/SYSTEM_DATAFLOW.md,
  docs/RESUME_MASTERPROMPT_19072026.md, docs/briefs/BRIEF_LACZNIK_ETAP2_22072026.md
