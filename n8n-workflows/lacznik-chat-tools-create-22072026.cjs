// BE-LACZNIK-E2 (22/07/2026, brief BRIEF_LACZNIK_ETAP2_22072026):
// tworzy NOWY, OSOBNY workflow "AGS Lacznik Chat Tools" (zero dotykania HITL i Schedulera).
//
// Zawartosc workflowu:
//   1. MCP Server Trigger (sciezka z sekretem = capability URL dla konektora claude.ai)
//      + 4 narzedzia HTTP (stan_gry, wyslij_raport_pracy oraz - od 31/07/2026 - para
//      zapisz_tekst + teczka) -> cienkie endpointy cm-agent
//      /lacznik/raport i /lacznik/stan (guard: sekret lacznik_e2_secret z app_secrets).
//   2. Wariant B (fallback bez MCP): webhook POST /webhook/chat-raport + GET /webhook/stan-gry
//      - czysty przelot do cm-agent, sekret przekazuje WOLAJACY (walidacja w cm-agent,
//      zero literalow sekretu w galeziach wariantu B).
//
// JAWNE ODSTEPSTWO od "zero literalow w definicjach" (udokumentowane w docs/komponenty/lacznik.md):
// wezly-narzedzia MCP wykonuja sie POJEDYNCZO (bez lancucha), wiec nie moga pobrac sekretu
// wezlem Postgres jak HITL - sekret lacznik_e2_secret stoi literalem w TYM JEDNYM dedykowanym
// workflow (path triggera + naglowek narzedzi). Zrodlem prawdy pozostaje app_secrets
// (cm-agent waliduje z DB); rotacja = UPDATE app_secrets + ponowne uruchomienie tego skryptu
// z LACZNIK_E2_SECRET=<nowy>. saveDataSuccessExecution=none (tresci raportow nie leza w logach).
//
// URUCHOMIENIE (Git Bash / node na maszynie z .env):
//   set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' "C:\Claude-CoWork\AGS\ags-agents\.env" | sed 's/\r$//') && set +a \
//     && node "C:\Claude-CoWork\AGS\ags-agents\n8n-workflows\lacznik-chat-tools-create-22072026.cjs"
// Rotacja sekretu: jak wyzej, ale z LACZNIK_E2_SECRET=<nowy> w env przed node. BEZ tej zmiennej
// skrypt PRZEJMUJE sekret z zywego workflow, wiec adres konektora claude.ai zostaje nietkniety
// (od 31/07 - wczesniej kazde uruchomienie losowalo nowy sekret i zrywalo polaczenie).
// Skrypt jest idempotentny: workflow o tej nazwie istnieje -> PUT (z backupem), nie duplikat.
// Po zapisie: deactivate+activate (kanon) + sonda MCP initialize/tools-list (dowod, ze trigger zyje).
const fs = require('fs');
const crypto = require('crypto');

const NAME = 'AGS Lacznik Chat Tools';
const CM = 'http://cm-agent:8089';

function buildWorkflow(secret) {
  const mcpPath = `lacznik-${secret}`;
  const nodes = [
    {
      name: 'MCP Lacznik', type: '@n8n/n8n-nodes-langchain.mcpTrigger', typeVersion: 2,
      position: [0, 0], webhookId: crypto.randomUUID(),
      parameters: { path: mcpPath },
    },
    {
      name: 'stan_gry', type: 'n8n-nodes-base.httpRequestTool', typeVersion: 4.2,
      position: [-180, 260],
      parameters: {
        toolDescription: 'Pobiera aktualny stan gry AGS z bazy serwera (plan tygodnia, kolejka, publikacje z metrykami, kontakty w grze, otwarte decyzje, lejek sprzedaży, radar). Wołaj NA STARCIE sesji pracy. Parametr scope: x, linkedin, sprzedaz albo all.',
        method: 'GET',
        url: `${CM}/lacznik/stan`,
        sendQuery: true,
        queryParameters: { parameters: [
          { name: 'scope', value: "={{ $fromAI('scope', 'Zakres stanu gry: x, linkedin, sprzedaz albo all', 'string') }}" },
        ] },
        sendHeaders: true,
        headerParameters: { parameters: [ { name: 'X-Lacznik-Secret', value: secret } ] },
        options: {},
      },
    },
    {
      name: 'wyslij_raport_pracy', type: 'n8n-nodes-base.httpRequestTool', typeVersion: 4.2,
      position: [180, 260],
      parameters: {
        toolDescription: 'Wysyła blok [RAPORT PRACY v1] do systemu AGS (parser zapisuje komentarze, DM-y, reakcje, zaproszenia, nowe osoby i obserwacje; duplikaty pomija). Wołaj NA KONIEC sesji pracy z pełnym blokiem od [RAPORT PRACY v1] do [KONIEC RAPORTU]. Zwraca potwierdzenie z licznikami - streść je użytkownikowi.',
        method: 'POST',
        url: `${CM}/lacznik/raport`,
        sendHeaders: true,
        headerParameters: { parameters: [ { name: 'X-Lacznik-Secret', value: secret } ] },
        sendBody: true,
        specifyBody: 'json',
        jsonBody: "={{ JSON.stringify({ kanal: $fromAI('kanal', 'Kanal pracy: x, linkedin albo sprzedaz', 'string'), raport: $fromAI('raport_md', 'Pelny blok raportu od [RAPORT PRACY v1] do [KONIEC RAPORTU], markdown', 'string') }) }}",
        options: {},
      },
    },
    // ---- Teczka prospekta (31/07/2026): para zapisz/odczyt JEDNEGO kontraktu ----
    // Powod: teksty sprzedazowe pisane w czacie ladowaly tylko w czacie. Zero sladu w bazie,
    // wiec nie dalo sie iterowac, policzyc ani wczytac w nowej rozmowie.
    // neverError: bledy kontraktu (nieznany kontakt) wracaja jako TRESC z lista podobnych -
    // czat ma je pokazac czlowiekowi, a nie polec na "tool call failed".
    {
      name: 'zapisz_tekst', type: 'n8n-nodes-base.httpRequestTool', typeVersion: 4.2,
      position: [540, 260],
      parameters: {
        toolDescription: 'Zapisuje w bazie tekst wysłany do kontaktu (mail, SMS, WhatsApp, DM, notatka z telefonu) razem z datą i statusem. Wołaj ZAWSZE po napisaniu tekstu sprzedażowego, także szkicu - inaczej tekst zostaje wyłącznie w czacie i przepada. Kontakt podaj nazwą albo UUID; jeśli nie istnieje, dostaniesz listę podobnych i NIC nie zostanie zapisane - nigdy nie zakładaj nowego kontaktu na siłę. UWAGA: n8n wymaga wszystkich parametrów, więc dla tych, które nie dotyczą (temat, next_step, next_step_date), podaj PUSTY CIĄG - system potraktuje je jak brak i niczego nie nadpisze.',
        method: 'POST',
        url: `${CM}/lacznik/zapisz-tekst`,
        sendHeaders: true,
        headerParameters: { parameters: [ { name: 'X-Lacznik-Secret', value: secret } ] },
        sendBody: true,
        specifyBody: 'json',
        // Nazwy kluczy $fromAI SA nazwami parametrow, ktore widzi wolajacy - musza byc DOKLADNIE
        // takie, jak kontrakt uzgodniony z Managerem (`contact_id`), inaczej wola nazwa z kontraktu
        // i dostaje blad schematu. Zlapane tap-testem 31/07 (parametr nazywal sie `kontakt`).
        // n8n oznacza KAZDY parametr $fromAI jako wymagany i nie ma sposobu na opcjonalny
        // (docs "Let AI specify tool parameters"; `isOptional` to otwarty wniosek o funkcje),
        // dlatego opcjonalnosc realizujemy PUSTYM CIAGIEM, ktory serwer traktuje jak brak.
        jsonBody: "={{ JSON.stringify({ contact_id: $fromAI('contact_id', 'Nazwa prospekta albo UUID z lejka lub kontaktow', 'string'), kanal: $fromAI('kanal', 'Kanal: email, sms, whatsapp, dm albo telefon', 'string'), tresc: $fromAI('tresc', 'Pelna tresc tekstu, ktory poszedl albo ma pojsc do kontaktu', 'string'), status: $fromAI('status', 'draft gdy szkic, sent gdy juz wyslane', 'string'), temat: $fromAI('temat', 'Temat wiadomosci. PUSTY CIAG jesli nie dotyczy', 'string'), next_step: $fromAI('next_step', 'Nastepny ustalony krok. PUSTY CIAG jesli nie ustalasz', 'string'), next_step_date: $fromAI('next_step_date', 'Termin nastepnego kroku RRRR-MM-DD GG:MM. PUSTY CIAG jesli nie ustalasz', 'string') }) }}",
        options: { response: { response: { neverError: true } } },
      },
    },
    {
      name: 'teczka', type: 'n8n-nodes-base.httpRequestTool', typeVersion: 4.2,
      position: [900, 260],
      parameters: {
        toolDescription: 'Zwraca w JEDNYM wywołaniu całą teczkę kontaktu: dane, wszystko co do niego poszło chronologicznie, ostatni ustalony następny krok z datą oraz status. Wołaj ZANIM napiszesz cokolwiek do prospekta - bez tego nie wiesz, co już dostał ani co obiecaliśmy. Kontakt podaj nazwą albo UUID.',
        method: 'GET',
        url: `${CM}/lacznik/teczka`,
        sendHeaders: true,
        headerParameters: { parameters: [ { name: 'X-Lacznik-Secret', value: secret } ] },
        sendQuery: true,
        queryParameters: { parameters: [
          { name: 'kontakt', value: "={{ $fromAI('contact_id', 'Nazwa prospekta albo UUID z lejka lub kontaktow', 'string') }}" },
        ] },
        options: { response: { response: { neverError: true } } },
      },
    },
    // ---- Wariant B: fallback bez MCP (ChatGPT Action / dowolny klient HTTP) ----
    {
      name: 'Webhook Chat Raport', type: 'n8n-nodes-base.webhook', typeVersion: 2,
      position: [0, 520], webhookId: crypto.randomUUID(),
      parameters: { httpMethod: 'POST', path: 'chat-raport', responseMode: 'responseNode', options: {} },
    },
    {
      name: 'Forward Raport', type: 'n8n-nodes-base.httpRequest', typeVersion: 4.2,
      position: [220, 520],
      parameters: {
        method: 'POST',
        url: `=${CM}/lacznik/raport?secret={{ encodeURIComponent($json.body.secret || '') }}`,
        sendBody: true, specifyBody: 'json',
        jsonBody: "={{ JSON.stringify({ kanal: $json.body.kanal || '', raport: $json.body.raport || $json.body.raport_md || '' }) }}",
        options: { response: { response: { neverError: true } } },
      },
    },
    {
      name: 'Respond Raport', type: 'n8n-nodes-base.respondToWebhook', typeVersion: 1.1,
      position: [440, 520],
      parameters: { respondWith: 'json', responseBody: '={{ JSON.stringify($json) }}', options: {} },
    },
    {
      name: 'Webhook Stan Gry', type: 'n8n-nodes-base.webhook', typeVersion: 2,
      position: [0, 720], webhookId: crypto.randomUUID(),
      parameters: { httpMethod: 'GET', path: 'stan-gry', responseMode: 'responseNode', options: {} },
    },
    {
      name: 'Forward Stan', type: 'n8n-nodes-base.httpRequest', typeVersion: 4.2,
      position: [220, 720],
      parameters: {
        method: 'GET',
        url: `=${CM}/lacznik/stan?scope={{ encodeURIComponent($json.query.scope || 'all') }}&secret={{ encodeURIComponent($json.query.secret || '') }}`,
        options: { response: { response: { neverError: true } } },
      },
    },
    {
      name: 'Respond Stan', type: 'n8n-nodes-base.respondToWebhook', typeVersion: 1.1,
      position: [440, 720],
      parameters: { respondWith: 'json', responseBody: '={{ JSON.stringify($json) }}', options: {} },
    },
  ];
  const connections = {
    'stan_gry': { ai_tool: [[{ node: 'MCP Lacznik', type: 'ai_tool', index: 0 }]] },
    'wyslij_raport_pracy': { ai_tool: [[{ node: 'MCP Lacznik', type: 'ai_tool', index: 0 }]] },
    'zapisz_tekst': { ai_tool: [[{ node: 'MCP Lacznik', type: 'ai_tool', index: 0 }]] },
    'teczka': { ai_tool: [[{ node: 'MCP Lacznik', type: 'ai_tool', index: 0 }]] },
    'Webhook Chat Raport': { main: [[{ node: 'Forward Raport', type: 'main', index: 0 }]] },
    'Forward Raport': { main: [[{ node: 'Respond Raport', type: 'main', index: 0 }]] },
    'Webhook Stan Gry': { main: [[{ node: 'Forward Stan', type: 'main', index: 0 }]] },
    'Forward Stan': { main: [[{ node: 'Respond Stan', type: 'main', index: 0 }]] },
  };
  const settings = {
    saveDataSuccessExecution: 'none', saveDataErrorExecution: 'all',
    saveManualExecutions: false, timezone: 'Europe/Warsaw', executionOrder: 'v1',
  };
  return { name: NAME, nodes, connections, settings };
}

async function mcpProbe(base, mcpPath) {
  // Sonda streamable HTTP: initialize -> tools/list. Dowod, ze trigger zyje i narzedzia sa widoczne.
  const url = `${base}/mcp/${mcpPath}`;
  const H = { 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream' };
  const init = await fetch(url, { method: 'POST', headers: H, body: JSON.stringify({
    jsonrpc: '2.0', id: 1, method: 'initialize', params: {
      protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'lacznik-probe', version: '1.0' } } }) });
  const sid = init.headers.get('mcp-session-id');
  const initText = await init.text();
  console.log('MCP initialize:', init.status, sid ? `session=${sid.slice(0, 8)}...` : '(bez session id)');
  if (init.status >= 400) { console.log(initText.slice(0, 400)); return false; }
  const H2 = sid ? { ...H, 'mcp-session-id': sid } : H;
  await fetch(url, { method: 'POST', headers: H2, body: JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) });
  const list = await fetch(url, { method: 'POST', headers: H2, body: JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'tools/list' }) });
  const listText = await list.text();
  const toolNames = [...listText.matchAll(/"name"\s*:\s*"([^"]+)"/g)].map(m => m[1]).filter(n => !/probe/.test(n));
  console.log('MCP tools/list:', list.status, '| narzedzia:', [...new Set(toolNames)].join(', ') || '(brak - sprawdz recznie)');
  return list.status < 400 && toolNames.includes('stan_gry') && toolNames.includes('wyslij_raport_pracy');
}

async function main() {
  const base = process.env.N8N_BASE_URL, key = process.env.N8N_API_KEY;
  if (!base || !key) { console.log('BRAK N8N_BASE_URL / N8N_API_KEY w env'); process.exit(1); }
  const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };

  // idempotencja: szukaj po nazwie
  const all = await (await fetch(`${base}/api/v1/workflows?limit=250`, { headers: H })).json();
  const existing = (all.data || []).find(w => w.name === NAME);

  // SEKRET: jawna rotacja z env > sekret ZYWEGO workflow > dopiero na koncu nowy.
  // 31/07/2026: srodkowego czlonu nie bylo, wiec KAZDE ponowne uruchomienie skryptu losowalo
  // nowy sekret. A sekret siedzi w sciezce triggera, wiec zmienial sie adres konektora
  // claude.ai i rozjezdzal z wartoscia w app_secrets - czyli dolozenie jednego narzedzia
  // zrywalo Managerowi polaczenie. Skrypt idempotentny musi byc idempotentny takze w tym.
  let secret = (process.env.LACZNIK_E2_SECRET || '').trim();
  let zrodlo = secret ? 'env (jawna rotacja - adres konektora SIE ZMIENI)' : '';
  if (!secret && existing) {
    const live0 = await (await fetch(`${base}/api/v1/workflows/${existing.id}`, { headers: H })).json();
    const trig = (live0.nodes || []).find(n => (n.type || '').includes('mcpTrigger'));
    const p = (((trig || {}).parameters) || {}).path || '';
    if (p.startsWith('lacznik-')) {
      secret = p.slice('lacznik-'.length);
      zrodlo = 'zywy workflow (adres konektora BEZ ZMIAN)';
    }
  }
  if (!secret) {
    secret = crypto.randomBytes(24).toString('hex');
    zrodlo = 'NOWY - trzeba wpisac do app_secrets i przepiac konektor';
  }
  console.log('sekret z:', zrodlo);
  const wf = buildWorkflow(secret);
  let id;
  if (existing) {
    id = existing.id;
    const live = await (await fetch(`${base}/api/v1/workflows/${id}`, { headers: H })).json();
    fs.writeFileSync(`${__dirname}/bk_lacznik_chat_tools_${Date.now()}.json`, JSON.stringify(live));
    const r = await fetch(`${base}/api/v1/workflows/${id}`, { method: 'PUT', headers: H, body: JSON.stringify(wf) });
    console.log('PUT (istniejacy):', r.status, '| id:', id);
    if (r.status !== 200) { console.log((await r.text()).slice(0, 600)); process.exit(1); }
  } else {
    const r = await fetch(`${base}/api/v1/workflows`, { method: 'POST', headers: H, body: JSON.stringify(wf) });
    const created = await r.json();
    id = created.id;
    console.log('POST (nowy):', r.status, '| id:', id);
    if (r.status >= 300 || !id) { console.log(JSON.stringify(created).slice(0, 600)); process.exit(1); }
  }

  // kanon: deactivate+activate po kazdym zapisie
  let active = false;
  for (let i = 0; i < 3; i++) {
    await fetch(`${base}/api/v1/workflows/${id}/deactivate`, { method: 'POST', headers: H });
    const on = await fetch(`${base}/api/v1/workflows/${id}/activate`, { method: 'POST', headers: H });
    console.log('activate:', on.status);
    if (on.status === 200) { active = true; break; }
    console.log((await on.text()).slice(0, 500));
    await new Promise(res => setTimeout(res, 2000));
  }
  const chk = await (await fetch(`${base}/api/v1/workflows/${id}`, { headers: H })).json();
  console.log('verify: active:', chk.active, '| nodes:', (chk.nodes || []).length);

  // kopia w repo BEZ sekretu (placeholder) - sekret nie trafia do Gita
  const sanitized = JSON.parse(JSON.stringify(buildWorkflow('<LACZNIK_E2_SECRET>')));
  fs.writeFileSync(`${__dirname}/lacznik-chat-tools.json`, JSON.stringify(sanitized, null, 2));

  const mcpPath = `lacznik-${secret}`;
  let probeOk = false;
  if (active) { try { probeOk = await mcpProbe(base, mcpPath); } catch (e) { console.log('sonda MCP:', e.message); } }

  console.log('\n================ DLA TOMASZA ================');
  console.log('URL konektora (claude.ai -> Settings -> Connectors -> Add custom connector):');
  console.log(`  ${base}/mcp/${mcpPath}`);
  console.log('\nSQL (SSH, wklej w calosci) - sekret do app_secrets (guard cm-agent):');
  console.log(`  docker exec -i pg_n8n psql -U n8n -d ags_crd -c "INSERT INTO app_secrets (key, value) VALUES ('lacznik_e2_secret', '${secret}') ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value;"`);
  console.log('\nWariant B (fallback, sekret podaje wolajacy):');
  console.log(`  POST ${base}/webhook/chat-raport   body: {"secret":"...","kanal":"x","raport":"[RAPORT PRACY v1] ..."}`);
  console.log(`  GET  ${base}/webhook/stan-gry?secret=...&scope=x`);
  console.log('\nSonda MCP (initialize + tools/list):', probeOk ? 'PASS' : 'NIE POTWIERDZONA - patrz wyzej');
}
main().catch(e => { console.error(e.message); process.exit(1); });
