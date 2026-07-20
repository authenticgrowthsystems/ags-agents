// BE-ENGAGEMENT (20/07/2026, brief BRIEF_ENGAGEMENT_CRM_20072026 pkt D):
// album Telegram (media_group_id) = JEDEN post. Patch dopisuje media_group_id do
// metadata.media w wezle 'Prepare Idea Photo' workflowu HITL (U5pUZjy2yAhR1sWg).
// ZERO nowych wezlow, zero zmian routingu (AP-301-safe) - tylko jsCode jednego Code node.
// cm-agent grupuje potem zrzuty po metadata->'media'->>'media_group_id' i robi JEDNA analize.
// Bez tego patcha app dziala dalej: zrzuty osobne w <60 s lapie pytanie 'jeden post czy rozne?'.
//
// URUCHOMIENIE (integrator, PowerShell -> Git Bash / node na maszynie z .env):
//   cd C:\Users\Admin\AppData\Local\Temp\ags-media-spike   (albo dowolny katalog roboczy)
//   set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' "C:\Claude-CoWork\AGS\ags-agents\.env" | sed 's/\r$//') && set +a \
//     && node "C:\Claude-CoWork\AGS\ags-agents\n8n-workflows\patches\hitl-photo-mediagroup-20072026.cjs"
// Po PUT skrypt sam robi deactivate+activate (kanon: PUT bez cyklu = stary snapshot dziala dalej).
const fs = require('fs');

async function main() {
  const base = process.env.N8N_BASE_URL, key = process.env.N8N_API_KEY;
  if (!base || !key) { console.log('BRAK N8N_BASE_URL / N8N_API_KEY w env'); process.exit(1); }
  const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };
  const w = await (await fetch(`${base}/api/v1/workflows/U5pUZjy2yAhR1sWg`, { headers: H })).json();
  fs.writeFileSync(`${__dirname}/bk_hitl_mediagroup_${Date.now()}.json`, JSON.stringify(w));

  const node = w.nodes.find(n => n.name === 'Prepare Idea Photo');
  if (!node) { console.log('NODE Prepare Idea Photo MISSING'); process.exit(1); }
  const code = node.parameters.jsCode || '';
  if (code.includes('media_group_id')) { console.log('JUZ ZAPATCHOWANE - nic nie robie'); process.exit(0); }
  const OLD = "meta = { chat_id: d.chat_id, telegram_msg_id: (t.message && t.message.message_id) || null, idea_type: 'photo', media: fileId ? { file_id: fileId, kind: 'photo' } : null };";
  const NEW = "meta = { chat_id: d.chat_id, telegram_msg_id: (t.message && t.message.message_id) || null, idea_type: 'photo', media: fileId ? { file_id: fileId, kind: 'photo', media_group_id: (t.message && t.message.media_group_id) || null } : null };";
  if (!code.includes(OLD)) { console.log('WZORZEC NIE PASUJE - sprawdz recznie jsCode Prepare Idea Photo'); process.exit(1); }
  node.parameters.jsCode = code.replace(OLD, NEW);

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
  }
}
main().catch(e => { console.error(e); process.exit(1); });
