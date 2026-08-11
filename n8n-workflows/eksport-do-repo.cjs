// EKSPORT ZYWYCH WORKFLOW n8n DO REPO - z bramka na sekrety (11/08/2026).
//
// PO CO. Eksporty w tym katalogu rozjechaly sie z produkcja o dwa miesiace: HITL Handler mial
// w repo 143 wezly, a zywy 254 - i wezla, ktory obsluguje guziki zatwierdzania, w repo NIE BYLO
// w ogole. Nowy czytajacy wyciaga z takiego pliku nieprawde o systemie.
//
// DLACZEGO NIE ZWYKLY `curl > plik`. Bo przy pierwszej probie takiego eksportu 11/08 skan
// znalazl w ZYWEJ definicji **token bota Telegrama wpisany na sztywno w 44 wezlach**
// (`parameters.url`, adres api.telegram.org/bot<TOKEN>/...). Zwykly zrzut wpisalby dzialajacy
// token do publicznego repozytorium. Token NIE byl wczesniej w historii gita - sprawdzone -
// i ten skrypt istnieje po to, zeby nigdy sie tam nie znalazl.
//
// BRAMKA PADA ZAMKNIETA (AP-314). Skrypt maskuje wzorce, ktore ZNA, a gdy po maskowaniu zostanie
// cokolwiek wygladajacego na sekret - **odmawia zapisu**. Lepszy brak eksportu niz eksport,
// ktory "chyba jest czysty".
//
// UZYCIE - z maszyny Tomasza (Git Bash), nie z serwera (tam nie ma node ani .env):
//   cd "C:/Claude-CoWork/AGS/ags-agents"
//   set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' .env | sed 's/\r$//') && set +a
//   node .claude/worktrees/sb-work/n8n-workflows/eksport-do-repo.cjs sprawdz   # tylko skan
//   node .claude/worktrees/sb-work/n8n-workflows/eksport-do-repo.cjs zapisz    # skan + zapis
//
// CZEGO TEN PLIK NIE ROBI: nie naprawia zrodla problemu. Token ma zniknac Z DEFINICJI
// (poswiadczenie n8n albo odczyt z `app_secrets`, tak jak zrobiono w Schedulerze 02/07).
// Maskowanie chroni repo, nie produkcje. Wpis: docs/ops/DLUG_TECHNICZNY.md D-017.

const fs = require('fs');
const path = require('path');

const CELE = [
  { id: 'U5pUZjy2yAhR1sWg', plik: 'x-agent/ags-hitl-handler-v1.json', nazwa: 'AGS HITL Handler v1.0' },
  { id: 'x1jJEbcWAe3FnpCa', plik: 'x-agent/ags-scheduler-v1.json', nazwa: 'AGS Scheduler v1' },
  { id: 'yxJUJmZpSUe0tw9K', plik: 'lacznik-chat-tools.json', nazwa: 'AGS Lacznik Chat Tools' },
];

// Wzorce, ktore UMIEMY zamaskowac. Kazdy ma czytelny zamiennik, zeby w repo bylo widac,
// ze cos tam bylo i co - a nie zeby wygladalo, jakby adres byl niepelny.
const MASKI = [
  [/\d{8,12}:AA[\w-]{20,}/g, '<TELEGRAM_BOT_TOKEN>'],
  [/sk-[A-Za-z0-9_-]{20,}/g, '<API_KEY>'],
  [/Bearer\s+[A-Za-z0-9._-]{20,}/g, 'Bearer <TOKEN>'],
];

// Wzorce, ktore po maskowaniu NIE MAJA prawa zostac. Trafienie = odmowa zapisu.
const PODEJRZANE = [
  [/[A-Za-z0-9+/]{60,}={0,2}/g, 'dlugi ciag base64'],
  [/(?:secret|password|passwd|apikey|api_key|token)\s*[:=]\s*["'][^"']{16,}["']/gi, 'przypisanie do pola sekretu'],
];

const base = process.env.N8N_BASE_URL;
const key = process.env.N8N_API_KEY;
if (!base || !key) { console.error('BRAK N8N_BASE_URL / N8N_API_KEY w srodowisku.'); process.exit(1); }

const KATALOG = __dirname;

async function pobierz(id) {
  const r = await fetch(`${base}/api/v1/workflows/${id}`, { headers: { 'X-N8N-API-KEY': key } });
  if (!r.ok) { console.error(`GET ${id} nieudany:`, r.status); process.exit(1); }
  return r.json();
}

function oczysc(w) {
  // `activeVersion` to PELNA kopia definicji (migawka wersji uruchomionej) - podwaja rozmiar
  // pliku i czyni diffy nieczytelnymi. Zostaje `versionId`, wiec wiadomo, ktora wersja to jest.
  const { activeVersion, shared, ...reszta } = w;
  return reszta;
}

async function zrob(zapisywac) {
  let bledy = 0;
  for (const cel of CELE) {
    const w = oczysc(await pobierz(cel.id));
    let tekst = JSON.stringify(w, null, 2);

    const zamaskowane = [];
    for (const [re, na] of MASKI) {
      const m = tekst.match(re);
      if (m) { zamaskowane.push(`${na} x${m.length}`); tekst = tekst.replace(re, na); }
    }

    const zostalo = [];
    for (const [re, opis] of PODEJRZANE) {
      const m = tekst.match(re);
      if (m) zostalo.push(`${opis} x${m.length} (np. ${m[0].slice(0, 12)}...)`);
    }

    const kb = (tekst.length / 1024).toFixed(0);
    console.log(`\n${cel.nazwa}  (${w.nodes.length} wezlow, ${kb} KB)`);
    console.log(`  zamaskowane : ${zamaskowane.join(', ') || 'nic'}`);
    console.log(`  podejrzane  : ${zostalo.join(', ') || 'nic'}`);

    if (zostalo.length) {
      console.error('  ODMAWIAM ZAPISU tego pliku - zostal ciag, ktorego nie umiem rozpoznac.');
      console.error('  Przejrzyj go recznie w n8n. Lepszy brak eksportu niz eksport "chyba czysty".');
      bledy++;
      continue;
    }
    if (!zapisywac) { console.log('  (tryb sprawdz - nic nie zapisuje)'); continue; }

    const sciezka = path.join(KATALOG, cel.plik);
    fs.writeFileSync(sciezka, tekst + '\n');
    console.log(`  ZAPISANE -> n8n-workflows/${cel.plik}`);
  }
  console.log(bledy ? `\nPliki odrzucone: ${bledy}. Zapis niepelny.` : '\nWszystkie pliki czyste.');
  process.exit(bledy ? 1 : 0);
}

const tryb = process.argv[2];
if (tryb === 'sprawdz') zrob(false);
else if (tryb === 'zapisz') zrob(true);
else { console.log('Tryby: sprawdz | zapisz'); process.exit(1); }
