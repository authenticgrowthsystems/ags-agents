// BE-SPRZEDAWCA (20/07/2026, brief BRIEF_AGENT_SPRZEDAZY_MVP_20072026 pkt 3):
// przepustka komend sprzedazowych w Detect Update Type workflowu HITL (U5pUZjy2yAhR1sWg).
// DWIE edycje jsCode JEDNEGO wezla (waski wyjatek n8n z briefu; reszta HITL nietykalna):
//  1. /prospect /oferta /pipeline /add_sales_material -> plain_text (cm-agent ma dla nich
//     deterministyczne sciezki w sales.try_command; nieznane '/' wpadaly do 'other').
//  2. dokumenty .pdf (<=8MB) -> document_text (materialy sprzedazowe; cm-agent ekstrahuje
//     tekst przez pypdf w conversation.handle_document).
// ZERO nowych wezlow, zero zmian routingu (AP-301-safe). Wzorzec: hitl-karty-passthrough.cjs.
//
// URUCHOMIENIE (integrator, Git Bash / node na maszynie z .env):
//   set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' "C:\Claude-CoWork\AGS\ags-agents\.env" | sed 's/\r$//') && set +a \
//     && node "C:\Claude-CoWork\AGS\ags-agents\n8n-workflows\patches\hitl-sales-commands-20072026.cjs"
// Po PUT skrypt sam robi deactivate+activate (kanon: PUT bez cyklu = stary snapshot dziala dalej).
const fs = require('fs');

async function main() {
  const base = process.env.N8N_BASE_URL, key = process.env.N8N_API_KEY;
  if (!base || !key) { console.log('BRAK N8N_BASE_URL / N8N_API_KEY w env'); process.exit(1); }
  const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };
  const w = await (await fetch(`${base}/api/v1/workflows/U5pUZjy2yAhR1sWg`, { headers: H })).json();
  fs.writeFileSync(`${__dirname}/bk_hitl_sales_${Date.now()}.json`, JSON.stringify(w));

  const n = w.nodes.find(x => x.name === 'Detect Update Type');
  if (!n) { console.log('NODE Detect Update Type MISSING'); process.exit(1); }
  let code = n.parameters.jsCode || '';
  let changed = false;

  // 1) komendy sprzedazowe do przepustki plain_text
  const OLD1 = "if (txt.startsWith('/plan') || txt.startsWith('/cancel') || txt.startsWith('/kolejka') || txt.startsWith('/raport') || txt.startsWith('/karty') || txt.startsWith('/schowek') || txt.startsWith('/decyzje') || txt.startsWith('/brand'))";
  const NEW1 = "if (txt.startsWith('/plan') || txt.startsWith('/cancel') || txt.startsWith('/kolejka') || txt.startsWith('/raport') || txt.startsWith('/karty') || txt.startsWith('/schowek') || txt.startsWith('/decyzje') || txt.startsWith('/brand') || txt.startsWith('/prospect') || txt.startsWith('/oferta') || txt.startsWith('/pipeline') || txt.startsWith('/add_sales_material'))";
  if (code.includes("startsWith('/prospect')")) {
    console.log('1) komendy JUZ ZAPATCHOWANE');
  } else if (code.includes(OLD1)) {
    code = code.replace(OLD1, NEW1);
    changed = true;
    console.log('1) komendy sprzedazowe dopisane do przepustki');
  } else { console.log('1) ANCHOR plain_text NIE PASUJE - sprawdz recznie jsCode'); process.exit(1); }

  // 2) PDF-y do galezi document_text (materialy sprzedazowe)
  const OLD2 = "if (/\\.(md|txt)$/i.test(fn) && (d.file_size || 0) <= 120000)";
  const NEW2 = "if ((/\\.(md|txt)$/i.test(fn) && (d.file_size || 0) <= 120000) || (/\\.pdf$/i.test(fn) && (d.file_size || 0) <= 8000000))";
  if (code.includes('.pdf$')) {
    console.log('2) PDF JUZ ZAPATCHOWANY');
  } else if (code.includes(OLD2)) {
    code = code.replace(OLD2, NEW2);
    changed = true;
    console.log('2) PDF dopuszczony do document_text (<=8MB)');
  } else { console.log('2) ANCHOR document NIE PASUJE - sprawdz recznie jsCode'); process.exit(1); }

  if (!changed) { console.log('NIC DO ZROBIENIA - koncze bez PUT'); process.exit(0); }
  n.parameters.jsCode = code;

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
  console.log('verify: active:', chk.active,
    '| /prospect:', js.includes("startsWith('/prospect')"),
    '| pdf:', js.includes('.pdf$'));
}
main().catch(e => { console.error(e.message); process.exit(1); });
