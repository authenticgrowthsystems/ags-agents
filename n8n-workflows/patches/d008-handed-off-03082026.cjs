// D-008 (03/08/2026): przemianowanie WARTOSCI content_items.status w ZYWYM workflow n8n.
//
// CO TU JEST NAPRAWDE TRUDNE. Workflow "AGS Scheduler v1" (x1jJEbcWAe3FnpCa) ma w JEDNYM
// zapytaniu OBIE wartosci o tej samej nazwie, nalezace do DWOCH ROZNYCH slownikow:
//
//   UPDATE content_items ci SET status='published'
//    WHERE ci.id = (...) AND ci.status='dispatching'                    <-- TO zmieniamy
//      AND NOT EXISTS (SELECT 1 FROM post_queue q WHERE q.content_item_id=ci.id
//                       AND q.status IN ('review','scheduled','queued','dispatching'));  <-- TO zostaje
//
// Zwykla podmiana napisu w tresci wezla zerwalaby dopasowanie w kolejce publikacji - po cichu,
// bez bledu, bo SQL nadal bylby poprawny. Dlatego skrypt podmienia WYLACZNIE `ci.status='...'`
// i sam siebie sprawdza: odmawia dzialania, jesli liczby nie zgadzaja sie co do jednego.
//
// UZYCIE (Bash, z katalogu repozytorium):
//   set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' \
//       "C:/Claude-CoWork/AGS/ags-agents/.env" | sed 's/\r$//') && set +a
//   node n8n-workflows/patches/d008-handed-off-03082026.cjs sprawdz   # tylko odczyt
//   node n8n-workflows/patches/d008-handed-off-03082026.cjs wylacz    # przed migracja danych
//   node n8n-workflows/patches/d008-handed-off-03082026.cjs patch     # PUT, zostawia WYLACZONY
//   node n8n-workflows/patches/d008-handed-off-03082026.cjs wlacz     # po starcie cm-agenta
//   node n8n-workflows/patches/d008-handed-off-03082026.cjs cofnij    # ratunek: powrot do starej
//
// DLACZEGO `patch` NIE WLACZA SAM. Kolejnosc w oknie jest scisla: workflow wraca do gry DOPIERO
// gdy stoi juz nowy obraz cm-agenta. Gdyby skrypt wlaczal go od razu, Scheduler przez chwile
// pisalby nowa wartosc do systemu, w ktorym pisarz jeszcze jej nie zna.
//
// PAMIETAJ (project_n8n_reactivate_after_put): PUT zapisuje definicje do bazy, ale AKTYWNY
// snapshot trzyma STARA. Dopoki nie przejdzie activate, workflow wykonuje wersje sprzed PUT-a.
// Dlatego `wlacz` nie ufa odpowiedzi 200 ani fladze "active" - czeka na NOWE WYKONANIE.

const fs = require('fs');

const ID = 'x1jJEbcWAe3FnpCa';
const NAZWA = 'AGS Scheduler v1';
const WEZLY = ['Mark Published', 'Mark Published LI'];

const STARA = "ci.status='dispatching'";
const NOWA = "ci.status='handed_off'";
// Fragment KOLEJKI, ktory ma przetrwac patch w nienaruszonym stanie - liczymy go przed i po.
const KOLEJKA = "q.status IN ('review','scheduled','queued','dispatching')";

const ALLOWED = ['saveDataErrorExecution', 'saveDataSuccessExecution', 'saveManualExecutions',
  'saveExecutionProgress', 'executionTimeout', 'errorWorkflow', 'timezone', 'executionOrder'];

const base = process.env.N8N_BASE_URL;
const key = process.env.N8N_API_KEY;
if (!base || !key) { console.error('BRAK N8N_BASE_URL / N8N_API_KEY w srodowisku.'); process.exit(1); }
const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };

const ile = (s, igla) => s.split(igla).length - 1;
const spij = (ms) => new Promise(r => setTimeout(r, ms));

async function pobierz() {
  const r = await fetch(`${base}/api/v1/workflows/${ID}`, { headers: H });
  if (!r.ok) { console.error('GET nieudany:', r.status, await r.text()); process.exit(1); }
  return r.json();
}

function policz(w) {
  let stare = 0, nowe = 0, kolejka = 0;
  for (const n of w.nodes) {
    const q = (n.parameters && n.parameters.query) || '';
    stare += ile(q, STARA); nowe += ile(q, NOWA); kolejka += ile(q, KOLEJKA);
  }
  return { stare, nowe, kolejka };
}

async function wykonania(limit = 3) {
  const r = await fetch(`${base}/api/v1/executions?workflowId=${ID}&limit=${limit}`, { headers: H });
  const d = await r.json();
  return (d.data || []).map(e => ({ id: e.id, status: e.status, start: e.startedAt, stop: e.stoppedAt }));
}

async function sprawdz(cisza) {
  const w = await pobierz();
  const c = policz(w);
  if (!cisza) {
    console.log(`${NAZWA} | aktywny: ${w.active} | wezlow: ${w.nodes.length}`);
    console.log(`  ci.status='dispatching' (do zmiany) : ${c.stare}`);
    console.log(`  ci.status='handed_off'  (docelowo 2): ${c.nowe}`);
    console.log(`  lista statusow KOLEJKI   (ma byc 2) : ${c.kolejka}`);
    const e = await wykonania();
    console.log('  ostatnie wykonania:', e.map(x => `${x.id}/${x.status}/${x.start}`).join('  '));
  }
  return { w, c };
}

async function wylacz() {
  const e0 = await wykonania(1);
  console.log('ostatnie wykonanie przed wylaczeniem:', e0[0] ? `${e0[0].id} ${e0[0].status}` : '(brak)');
  if (e0[0] && !e0[0].stop) {
    // POLECENIE TOMASZA 03/08: wykonanie W LOCIE zostawiamy w spokoju. Zabicie go kosztuje
    // duplikat PUBLICZNEGO posta - wiersz kolejki moze byc juz opublikowany na X, a jeszcze
    // nie oznaczony w bazie. Czekamy; cykl trwa okolo sekundy.
    console.log('UWAGA: wykonanie jeszcze trwa. CZEKAM - nie przerywam (duplikat publicznego posta).');
    for (let i = 0; i < 30 && !(await wykonania(1))[0].stop; i++) await spij(2000);
  }
  const r = await fetch(`${base}/api/v1/workflows/${ID}/deactivate`, { method: 'POST', headers: H });
  console.log('deactivate:', r.status);
  const w = await pobierz();
  console.log(w.active ? 'ZLE: workflow NADAL aktywny.' : 'OK: workflow wylaczony.');
  process.exit(w.active ? 1 : 0);
}

async function patch(kierunek) {
  const [z, na] = kierunek === 'cofnij' ? [NOWA, STARA] : [STARA, NOWA];
  const { w, c } = await sprawdz(true);
  const przed = policz(w);

  if (w.active) {
    console.error('STOP: workflow jest AKTYWNY. Najpierw: node ... wylacz');
    process.exit(1);
  }
  const oczekiwane = kierunek === 'cofnij' ? c.nowe : c.stare;
  if (oczekiwane !== 2) {
    console.error(`STOP: spodziewalem sie DOKLADNIE 2 wystapien "${z}" (po jednym na wezel), jest ${oczekiwane}.`);
    console.error('Definicja workflow jest inna, niz zakladal ten skrypt. NIE zgaduj - przeczytaj ja recznie.');
    process.exit(1);
  }

  const kopia = `${__dirname}/bk_scheduler_d008_${Date.now()}.json`;
  fs.writeFileSync(kopia, JSON.stringify(w, null, 2));
  console.log('kopia zapasowa:', kopia);

  let zmienionych = 0;
  for (const n of w.nodes) {
    if (!WEZLY.includes(n.name)) continue;
    const q = (n.parameters && n.parameters.query) || '';
    if (!q.includes(z)) { console.log(`  ${n.name}: brak wzorca, pomijam`); continue; }
    n.parameters.query = q.split(z).join(na);
    zmienionych++;
    console.log(`  ${n.name}: ${z}  ->  ${na}`);
  }
  if (zmienionych !== 2) {
    console.error(`STOP: zmienilem ${zmienionych} wezlow zamiast 2. Nic nie wysylam.`);
    process.exit(1);
  }

  const po = policz(w);
  if (po.kolejka !== przed.kolejka) {
    console.error(`STOP: lista statusow KOLEJKI zmienila sie (${przed.kolejka} -> ${po.kolejka}).`);
    console.error('To jest dokladnie ta wada, ktorej ten skrypt ma nie popelnic. Nic nie wysylam.');
    process.exit(1);
  }

  const settings = {};
  for (const k of ALLOWED) if (w.settings && w.settings[k] !== undefined) settings[k] = w.settings[k];
  const put = await fetch(`${base}/api/v1/workflows/${ID}`, { method: 'PUT', headers: H,
    body: JSON.stringify({ name: w.name, nodes: w.nodes, connections: w.connections, settings }) });
  console.log('PUT:', put.status);
  if (put.status !== 200) { console.error(await put.text()); process.exit(1); }

  // ODCZYT PO ZAPISIE: 200 znaczy "przyjalem", nie "zapisalem to, co myslisz".
  const kontrola = policz(await pobierz());
  console.log('po zapisie:', JSON.stringify(kontrola));
  const dobrze = kierunek === 'cofnij'
    ? (kontrola.stare === 2 && kontrola.nowe === 0 && kontrola.kolejka === przed.kolejka)
    : (kontrola.nowe === 2 && kontrola.stare === 0 && kontrola.kolejka === przed.kolejka);
  console.log(dobrze ? 'OK: definicja zapisana poprawnie, kolejka nietknieta.' : 'ZLE: definicja po zapisie nie zgadza sie.');
  console.log('Workflow zostaje WYLACZONY. Wlacz go dopiero po starcie nowego obrazu cm-agenta:');
  console.log('  node n8n-workflows/patches/d008-handed-off-03082026.cjs wlacz');
  process.exit(dobrze ? 0 : 1);
}

async function wlacz() {
  const przed = await wykonania(1);
  const ostatnie = przed[0] ? przed[0].id : null;
  const r = await fetch(`${base}/api/v1/workflows/${ID}/activate`, { method: 'POST', headers: H });
  console.log('activate:', r.status);

  // POLECENIE TOMASZA 03/08: aktywacje potwierdza ZACHOWANIE, nie odpowiedz 200 ani flaga
  // "active". Cron chodzi co minute, wiec nowe wykonanie ma sie pojawic w ciagu dwoch minut.
  console.log('czekam na NOWE wykonanie (do 150 s)...');
  for (let i = 0; i < 30; i++) {
    await spij(5000);
    const teraz = await wykonania(1);
    if (teraz[0] && teraz[0].id !== ostatnie) {
      console.log(`OK: nowe wykonanie ${teraz[0].id} (${teraz[0].status}) o ${teraz[0].start}`);
      const k = policz(await pobierz());
      console.log('definicja w bazie:', JSON.stringify(k));
      process.exit(0);
    }
  }
  console.error('ZLE: przez 150 s nie pojawilo sie zadne nowe wykonanie. Workflow moze byc martwy.');
  console.error('Sprawdz w panelu n8n. Publikacje stoja, dopoki tego nie naprawisz.');
  process.exit(1);
}

const tryb = (process.argv[2] || 'sprawdz').toLowerCase();
const tryby = {
  sprawdz: () => sprawdz(false).then(() => process.exit(0)),
  wylacz,
  patch: () => patch('patch'),
  cofnij: () => patch('cofnij'),
  wlacz,
};
if (!tryby[tryb]) {
  console.error('Tryby: sprawdz | wylacz | patch | wlacz | cofnij');
  process.exit(1);
}
tryby[tryb]().catch(e => { console.error(e.message); process.exit(1); });
