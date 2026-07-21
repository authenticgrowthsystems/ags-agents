// BE-LACZNIK (22/07/2026, brief BRIEF_LACZNIK_22072026 pkt 1.2):
// przepustka komendy /kontekst w Detect Update Type workflowu HITL (U5pUZjy2yAhR1sWg).
// JEDNA edycja jsCode JEDNEGO wezla (waski wyjatek n8n z briefu; reszta HITL nietykalna):
// /kontekst -> plain_text (cm-agent ma deterministyczna trase w conversation.handle;
// nieznane '/' wpadaja do 'other' i gina). Wklejka [RAPORT PRACY nie potrzebuje przepustki -
// to zwykly tekst, idzie plain_text od zawsze.
// ZERO nowych wezlow, zero zmian routingu (AP-301-safe). Wzorzec: hitl-sales-commands-20072026.cjs.
//
// URUCHOMIENIE (integrator, Git Bash / node na maszynie z .env):
//   set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' "C:\Claude-CoWork\AGS\ags-agents\.env" | sed 's/\r$//') && set +a \
//     && node "C:\Claude-CoWork\AGS\ags-agents\n8n-workflows\patches\hitl-kontekst-command-22072026.cjs"
// Po PUT skrypt sam robi deactivate+activate (kanon: PUT bez cyklu = stary snapshot dziala dalej).
const fs = require('fs');

async function main() {
  const base = process.env.N8N_BASE_URL, key = process.env.N8N_API_KEY;
  if (!base || !key) { console.log('BRAK N8N_BASE_URL / N8N_API_KEY w env'); process.exit(1); }
  const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };
  const w = await (await fetch(`${base}/api/v1/workflows/U5pUZjy2yAhR1sWg`, { headers: H })).json();
  fs.writeFileSync(`${__dirname}/bk_hitl_kontekst_${Date.now()}.json`, JSON.stringify(w));

  const n = w.nodes.find(x => x.name === 'Detect Update Type');
  if (!n) { console.log('NODE Detect Update Type MISSING'); process.exit(1); }
  let code = n.parameters.jsCode || '';

  // /kontekst do przepustki plain_text (kotwica = koniec lancucha po patchu sprzedazy 20/07)
  const OLD = "txt.startsWith('/add_sales_material'))";
  const NEW = "txt.startsWith('/add_sales_material') || txt.startsWith('/kontekst'))";
  if (code.includes("startsWith('/kontekst')")) {
    console.log('/kontekst JUZ ZAPATCHOWANY - koncze bez PUT');
    process.exit(0);
  }
  if (!code.includes(OLD)) {
    console.log('ANCHOR plain_text NIE PASUJE (spodziewany koniec: .../add_sales_material)) - sprawdz recznie jsCode');
    process.exit(1);
  }
  n.parameters.jsCode = code.replace(OLD, NEW);
  console.log('/kontekst dopisany do przepustki plain_text');

  const ALLOWED = ['saveDataErrorExecution','saveDataSuccessExecution','saveManualExecutions','saveExecutionProgress','executionTimeout','errorWorkflow','timezone','executionOrder'];
  const settings = {};
  for (const k of ALLOWED) if (w.settings && w.settings[k] !== undefined) settings[k] = w.settings[k];
  const r = await fetch(`${base}/api/v1/workflows/U5pUZjy2yAhR1sWg`, { method: 'PUT', headers: H,
    body: JSON.stringify({ name: w.name, nodes: w.nodes, connections: w.connections, settings }) });
  console.log('PUT:', r.status, '| nodes:', w.nodes.length);
  if (r.status !== 200) { console.log((await r.text()).slice(0, 500)); process.exit(1); }
  for (let i = 0; i < 3; i++) {
    await fetch(`${base}/api/v1/workflows/U5pUZjy2yAhR1sWg/deactivate`, { method: 'POST', headers: H });
    const on = await fetch(`${base}/api/v1/workflows/U5pUZjy2yAhR1sWg/activate`, { method: 'POST', headers: H });
    console.log('activate:', on.status);
    if (on.status === 200) break;
    await new Promise(res => setTimeout(res, 2000));
  }
  const chk = await (await fetch(`${base}/api/v1/workflows/U5pUZjy2yAhR1sWg`, { headers: H })).json();
  const js = chk.nodes.find(x => x.name === 'Detect Update Type').parameters.jsCode;
  console.log('verify: active:', chk.active, '| /kontekst:', js.includes("startsWith('/kontekst')"));
}
main().catch(e => { console.error(e.message); process.exit(1); });
