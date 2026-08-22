// EKSPORT ZYWYCH WORKFLOW n8n DO REPO - z bramka na sekrety (11/08/2026, bramka przepisana 22/08/2026).
//
// PO CO. Eksporty w tym katalogu rozjechaly sie z produkcja o dwa miesiace: HITL Handler mial
// w repo 143 wezly, a zywy 254 - i wezla, ktory obsluguje guziki zatwierdzania, w repo NIE BYLO
// w ogole. Nowy czytajacy wyciaga z takiego pliku nieprawde o systemie.
//
// DLACZEGO NIE ZWYKLY `curl > plik`. Bo przy pierwszej probie takiego eksportu 11/08 skan
// znalazl w ZYWEJ definicji **token bota Telegrama wpisany na sztywno w 44 wezlach**
// (`parameters.url`, adres api.telegram.org/bot<TOKEN>/...). Zwykly zrzut wpisalby dzialajacy
// token do repozytorium. Token NIE byl wczesniej w historii gita - sprawdzone - i ten skrypt
// istnieje po to, zeby nigdy sie tam nie znalazl.
//
// BRAMKA PADA ZAMKNIETA (AP-314). Skrypt maskuje wzorce, ktore ZNA, a gdy po maskowaniu zostanie
// cokolwiek wygladajacego na sekret - **odmawia zapisu**. Lepszy brak eksportu niz eksport,
// ktory "chyba jest czysty".
//
// DLACZEGO BRAMKA ZOSTALA PRZEPISANA 22/08 (D-026). Stara wersja pytala o KSZTALT PRZYPISANIA:
// `secret|token|api_key ... = "..."`. Nie miala prawa trafic w ksztalt, ktorego uzywa n8n,
// bo tam nazwa i wartosc stoja w OSOBNYCH polach:
//   { "name": "X-Lacznik-Secret", "value": "<48 znakow hex>" }
// Slowo `secret` siedzi po stronie NAZWY, wartosc pod kluczem `value`. Zywy sekret Lacznika
// przeszedl przez bramke bez slowa i wyladowal w repo. To AP-315 o warstwe nizej: tam walidator
// sprawdzal forme tekstu zamiast gatunku, tu maskownik sprawdzal forme PRZYPISANIA zamiast tego,
// CZYM JEST WARTOSC. Nowa bramka pyta o wartosc.
//
// UZYCIE - z maszyny Tomasza (Git Bash), nie z serwera (tam nie ma node ani .env):
//   cd "C:/Claude-CoWork/AGS/ags-agents"
//   set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' .env | sed 's/\r$//') && set +a
//   node n8n-workflows/eksport-do-repo.cjs sprawdz   # pobiera z n8n, tylko skan
//   node n8n-workflows/eksport-do-repo.cjs zapisz    # pobiera z n8n, skan + zapis
//   node n8n-workflows/eksport-do-repo.cjs skan <plik.json> [...]   # bez sieci, ta sama bramka
//
// Tryb `skan` nie dotyka sieci ani niczego nie zapisuje - przepuszcza PLIKI Z DYSKU przez
// identyczny tor (maski, potem bramka). Sluzy do dwoch rzeczy: sprawdzenia eksportu, ktory juz
// lezy w repo, i przetestowania samej bramki zlym wsadem, zanim sie jej zaufa (AP-314 punkt 1).
//
// PowerShell 5.1 (maszyna Tomasza) nie zna `&&`. Lancuch komend: `A; if ($?) { B }`.
//
// CZEGO TEN PLIK NIE ROBI: nie naprawia zrodla problemu. Sekret ma zniknac Z DEFINICJI
// (poswiadczenie n8n albo odczyt z `app_secrets`, tak jak zrobiono w Schedulerze 02/07).
// Maskowanie chroni repo, nie produkcje. Wpisy: docs/ops/DLUG_TECHNICZNY.md D-017 i D-026.

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

// ---------------------------------------------------------------------------
// BRAMKA. Pyta o WARTOSC, nie o nazwe pola.
// ---------------------------------------------------------------------------
//
// JEDNOSTKA POMIARU: **blok lity**, czyli nieprzerwany ciag [A-Za-z0-9]. Separatory
// (`-`, `_`, `.`, `/`, `:`) blok PRZERYWAJA i to jest caly trik, bo dziela swiat dokladnie tam,
// gdzie trzeba:
//   - UUID (8-4-4-4-12) rozpada sie na bloki 8/4/4/4/12 - najdluzszy ma 12 znakow, wiec zaden
//     identyfikator wezla, `versionId` ani `webhookId` nie ma JAK trafic w prog. Tego nie trzeba
//     wpisywac na zadna biala liste, to wynika z ksztaltu UUID-a.
//   - identyfikatory pisane recznie (`node-telegram-send-approval`) rozpadaja sie na slowa.
//   - sekret jest z definicji jednym litym blokiem losowych znakow, wiec zostaje w calosci.
//     Sekret schowany w dluzszym napisie tez, bo mierzymy bloki WEWNATRZ napisu:
//     `lacznik-<48 hex>` daje blok 48 i wpada.
//
// PROGI. Zmierzone na dziewieciu prawdziwych eksportach z tego katalogu:
//   prog 32 - 13 trafien, wszystkie to albo sekret, albo identyfikator zasobu Notion;
//   prog 24 - dochodzi wlasne slownictwo n8n (`predefinedCredentialType` ma 24 znaki);
//   prog 20 - dochodzi `continueRegularOutput`, `workflowsFromSameOwner` i kilkanascie innych.
// Bramka, ktora krzyczy przy kazdym eksporcie, zostanie wylaczona przez czlowieka i wtedy nie
// chroni niczego. Stad 32 dla bloku dowolnego. Osobno 24 dla bloku CZYSTO SZESNASTKOWEGO,
// bo 24 znaki hex to 96 bitow, a zaden wyraz ze slownika n8n nie jest szesnastkowy.
const PROG_BLOK = 32;
const PROG_HEX = 24;
const BLOK = new RegExp(`[A-Za-z0-9]{${PROG_HEX},}`, 'g');
const CZYSTY_HEX = /^([0-9a-f]+|[0-9A-F]+)$/;

// Wzorce dodatkowe. Zostaja z poprzedniej wersji, bo lapia to, czego blok lity nie zlapie:
// blob base64 (rozbijaja go znaki `+` i `/`) oraz KROTSZY sekret, ktory sam sie przedstawil
// nazwa zmiennej w kodzie wezla Code.
const BASE64 = [/[A-Za-z0-9+/]{60,}={0,2}/g, 'dlugi ciag base64'];
const SLOWA_SEKRETU = 'secret|sekret|password|passwd|haslo|pwd|token|apikey|api[_-]?key|access[_-]?key|private[_-]?key|consumer[_-]?key|client[_-]?secret|credential|bearer';
const PRZYPISANIE = [new RegExp(`(?:${SLOWA_SEKRETU})\\s*[:=]\\s*["'][^"']{16,}["']`, 'gi'), 'przypisanie do pola sekretu'];
const NAZWA_SEKRETU = new RegExp(`(?:${SLOWA_SEKRETU})`, 'i');

// BIALA LISTA NA KLUCZACH. Wylacznie klucze, ktore w n8n ZAWSZE niosa identyfikator maszynowy,
// i tylko dla wartosci o ksztalcie identyfikatora. Sekret podlozony pod `id` w ksztalcie innym
// niz UUID / 32 hex / 64 hex / krotki nanoid nadal wpada - biala lista zwalnia PARE
// (klucz, ksztalt), nie sam klucz.
const KLUCZE_TOZSAMOSCI = new Set([
  'id', 'versionId', 'activeVersionId', 'webhookId', 'workflowId', 'sourceWorkflowId',
  'projectId', 'instanceId', 'credentialId', 'templateId', 'cachedResultId', 'nodeId',
]);
const KSZTALT_TOZSAMOSCI = /^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[0-9a-f]{32}|[0-9a-f]{64}|[A-Za-z0-9]{1,24})$/;

// BIALA LISTA KONTEKSTOWA. Jedna pozycja, opisana z nazwiska. Identyfikator zasobu Notion to
// 32 znaki hex bez myslnikow, wiec KSZTALTEM nie rozni sie od sekretu - odroznia go tylko to,
// przy jakim adresie stoi. Wpuszczamy dokladnie 32 hex w napisie, ktory mowi o notion.com.
// Sekret Lacznika ma 48 znakow, wiec ta furtka go nie przepuszcza.
// Druga pozycja: ZASLEPKA w miejscu wartosci. `ags-hitl-timeout-checker-v1.json` ma w wezle
// Code cztery przypisania w rodzaju `accessTokenSecret = "__X_ACCESS_TOKEN_SECRET__"` i to nie
// sa sekrety, tylko puste miejsca do podstawienia. Wylapane na probie: bez tej pozycji bramka
// odmawiala eksportu pliku, w ktorym nie ma zadnego sekretu, a taka bramka zostaje wylaczona.
// Zaden prawdziwy sekret nie jest napisem WIELKIMI LITERAMI w podkresleniach albo nawiasach.
const ZASLEPKA = /^(__[A-Z0-9_]+__|<[A-Z0-9_]+>|\$\{[A-Za-z0-9_]+\}|YOUR_[A-Z0-9_]+|TWOJ_[A-Z0-9_]+|PLACEHOLDER|CHANGEME)$/;
const KONTEKST = [
  {
    nazwa: 'identyfikator zasobu Notion',
    test: (trafienie, napis) => trafienie.length === 32 && /^[0-9a-f]+$/.test(trafienie) && /notion\.com/i.test(napis),
  },
  {
    nazwa: 'zaslepka zamiast wartosci',
    test: (trafienie) => {
      const m = trafienie.match(/["']([^"']+)["']\s*$/);
      return ZASLEPKA.test(m ? m[1] : trafienie);
    },
  },
];

function wyrazenieN8n(s) {
  return s.startsWith('=') || s.includes('{{');
}

// Bialej listy pyta KAZDA regula, nie tylko blok lity. Inaczej `meta.instanceId` (64 znaki hex,
// odcisk instancji n8n, nie sekret) wpada w regule base64 i bramka krzyczy przy KAZDYM zywym
// eksporcie - wylapane na probie, zanim ktokolwiek jej zaufal (AP-314 punkt 1).
function zwolnione(trafienie, napis, klucz) {
  if (KLUCZE_TOZSAMOSCI.has(klucz) && KSZTALT_TOZSAMOSCI.test(napis)) return `klucz tozsamosci "${klucz}"`;
  for (const k of KONTEKST) if (k.test(trafienie, napis)) return k.nazwa;
  return null;
}

function podglad(s) {
  // NIGDY calosc. Tyle, zeby czlowiek rozpoznal, o ktora wartosc chodzi, i ani znaku wiecej.
  return s.length <= 12 ? s : `${s.slice(0, 12)}...`;
}

// Chodzi po DRZEWIE, nie po tekscie, zeby komunikat odmowy mogl podac sciezke do wartosci.
// Sciezka wezla dostaje nazwe z n8n, bo `nodes[17]` nie mowi czlowiekowi nic, a nazwa wezla
// jest tym, co widzi w edytorze.
function chodz(v, sciezka, klucz, zbior) {
  if (typeof v === 'string') {
    for (const blok of v.match(BLOK) || []) {
      const dosc = blok.length >= PROG_BLOK || (blok.length >= PROG_HEX && CZYSTY_HEX.test(blok));
      if (!dosc) continue;
      if (zwolnione(blok, v, klucz)) continue;
      zbior.push({ regula: 'lity blok o wysokiej entropii', sciezka, klucz, dlugosc: blok.length, poczatek: podglad(blok) });
    }
    for (const [re, opis] of [BASE64, PRZYPISANIE]) {
      for (const t of v.match(re) || []) {
        if (zwolnione(t, v, klucz)) continue;
        zbior.push({ regula: opis, sciezka, klucz, dlugosc: t.length, poczatek: podglad(t) });
      }
    }
    return;
  }
  if (Array.isArray(v)) {
    v.forEach((x, i) => {
      const etykieta = x && typeof x === 'object' && typeof x.name === 'string' ? `[${i}] "${x.name}"` : `[${i}]`;
      chodz(x, `${sciezka}${etykieta}`, klucz, zbior);
    });
    return;
  }
  if (v && typeof v === 'object') {
    // Ksztalt, o ktory potknela sie stara bramka: nazwa i wartosc w OSOBNYCH polach.
    // n8n trzyma tak naglowki HTTP, parametry zapytania i pola formularzy.
    if (typeof v.name === 'string' && typeof v.value === 'string'
        && NAZWA_SEKRETU.test(v.name) && v.value.length >= 16 && !wyrazenieN8n(v.value)
        && !/^<[A-Z_]+>$/.test(v.value)) {
      zbior.push({
        regula: `para nazwa/wartosc: pole "${v.name}" nazywa sie jak sekret`,
        sciezka: `${sciezka}.value`, klucz: 'value', dlugosc: v.value.length, poczatek: podglad(v.value),
      });
    }
    for (const [k, x] of Object.entries(v)) chodz(x, `${sciezka}.${k}`, k, zbior);
  }
}

// Zwraca liste znalezisk. Pusta lista = czysto. Nieparsowalny JSON to tez odmowa, bo bramka,
// ktora nie umie przeczytac wsadu, nie ma prawa powiedziec, ze wsad jest czysty.
function znajdzPodejrzane(tekst) {
  let drzewo;
  try {
    drzewo = JSON.parse(tekst);
  } catch (e) {
    return [{ regula: 'wsad nie jest poprawnym JSON-em, wiec nie umiem go sprawdzic', sciezka: '$', klucz: '-', dlugosc: tekst.length, poczatek: podglad(tekst.trim()) }];
  }
  const zbior = [];
  chodz(drzewo, '$', '$', zbior);
  // Ta sama wartosc moze trafic w dwie reguly naraz. Czlowiek ma zobaczyc miejsce raz.
  const widziane = new Set();
  return zbior.filter((z) => {
    const k = `${z.sciezka}|${z.poczatek}`;
    if (widziane.has(k)) return false;
    widziane.add(k);
    return true;
  });
}

function wypiszOdmowe(etykieta, znaleziska) {
  console.error(`  ODMAWIAM ZAPISU: ${etykieta}`);
  console.error('  Bramka pada zamknieta (AP-314): nie umiem uznac tych wartosci za bezpieczne.');
  for (const z of znaleziska) {
    console.error(`    - ${z.regula}`);
    console.error(`      sciezka  : ${z.sciezka}`);
    console.error(`      wartosc  : klucz "${z.klucz}", dlugosc ${z.dlugosc}, poczatek "${z.poczatek}" (reszty nie pokazuje celowo)`);
  }
  console.error('  CO Z TYM ZROBIC:');
  console.error('    1. Otworz workflow w n8n i znajdz wezel po nazwie ze sciezki (fragment `nodes[i] "..."`).');
  console.error('    2. Jesli to sekret: wyjmij go z definicji - poswiadczenie n8n albo odczyt z `app_secrets`');
  console.error('       wezlem Postgres, tak jak Scheduler od 02/07. Potem eksportuj ponownie.');
  console.error('    3. Jesli to identyfikator, a nie sekret: dopisz go do bialej listy w tym pliku');
  console.error('       (KLUCZE_TOZSAMOSCI albo KONTEKST) razem z uzasadnieniem. Bialej listy nie');
  console.error('       poszerzamy "na wszelki wypadek" - kazda pozycja ma byc opisana z nazwiska.');
  console.error('    4. Nie obchodz bramki recznym `curl > plik`. Ona jest po to, zeby to bylo trudne.');
}

function przepusc(surowy) {
  let tekst = surowy;
  const zamaskowane = [];
  for (const [re, na] of MASKI) {
    const m = tekst.match(re);
    if (m) { zamaskowane.push(`${na} x${m.length}`); tekst = tekst.replace(re, na); }
  }
  return { tekst, zamaskowane, znaleziska: znajdzPodejrzane(tekst) };
}

// ---------------------------------------------------------------------------
// Tor sieciowy: pobierz z n8n, przepusc przez bramke, zapisz.
// ---------------------------------------------------------------------------

function srodowisko() {
  const base = process.env.N8N_BASE_URL;
  const key = process.env.N8N_API_KEY;
  if (!base || !key) { console.error('BRAK N8N_BASE_URL / N8N_API_KEY w srodowisku.'); process.exit(1); }
  return { base, key };
}

const KATALOG = __dirname;

async function pobierz(base, key, id) {
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
  const { base, key } = srodowisko();
  let bledy = 0;
  for (const cel of CELE) {
    const w = oczysc(await pobierz(base, key, cel.id));
    const { tekst, zamaskowane, znaleziska } = przepusc(JSON.stringify(w, null, 2));

    const kb = (tekst.length / 1024).toFixed(0);
    console.log(`\n${cel.nazwa}  (${w.nodes.length} wezlow, ${kb} KB)`);
    console.log(`  zamaskowane : ${zamaskowane.join(', ') || 'nic'}`);
    console.log(`  podejrzane  : ${znaleziska.length ? `${znaleziska.length} miejsc` : 'nic'}`);

    if (znaleziska.length) {
      wypiszOdmowe(`n8n-workflows/${cel.plik}`, znaleziska);
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

// ---------------------------------------------------------------------------
// Tor offline: te same maski, ta sama bramka, pliki z dysku. Zero sieci, zero zapisu.
// ---------------------------------------------------------------------------

function skanuj(pliki) {
  if (!pliki.length) { console.error('Podaj co najmniej jeden plik: skan <plik.json> [...]'); process.exit(1); }
  let bledy = 0;
  for (const p of pliki) {
    let surowy;
    try {
      surowy = fs.readFileSync(p, 'utf8');
    } catch (e) {
      console.error(`\n${p}\n  NIE UMIEM PRZECZYTAC PLIKU: ${e.code || e.message}`);
      bledy++;
      continue;
    }
    const { zamaskowane, znaleziska } = przepusc(surowy);
    console.log(`\n${p}`);
    console.log(`  zamaskowane : ${zamaskowane.join(', ') || 'nic'}`);
    console.log(`  podejrzane  : ${znaleziska.length ? `${znaleziska.length} miejsc` : 'nic'}`);
    if (znaleziska.length) { wypiszOdmowe(p, znaleziska); bledy++; }
  }
  console.log(bledy ? `\nPliki, ktorych bramka by nie przepuscila: ${bledy}.` : '\nWszystkie pliki czyste.');
  process.exit(bledy ? 1 : 0);
}

const tryb = process.argv[2];
if (tryb === 'sprawdz') zrob(false);
else if (tryb === 'zapisz') zrob(true);
else if (tryb === 'skan') skanuj(process.argv.slice(3));
else { console.log('Tryby: sprawdz | zapisz | skan <plik.json> [...]'); process.exit(1); }
