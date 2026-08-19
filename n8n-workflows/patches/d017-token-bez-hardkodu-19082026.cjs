// D-017 (19/08/2026): token bota Telegrama wpisany NA SZTYWNO w 44 wezlach HITL Handlera.
//
// CO JEST DLUGIEM. Kanon projektu, powtorzony w trzech miejscach (SYSTEM_DATAFLOW,
// DEPLOY_CHECKLIST, komponenty/n8n-transport), brzmi: sekrety wylacznie w `app_secrets`,
// zero literalow w definicjach n8n. HITL Handler tego kanonu NIE spelnia: w 44 wezlach
// `httpRequest` adres wyglada tak
//     https://api.telegram.org/bot<TOKEN>/sendMessage
// czyli token siedzi w SCIEZCE URL, w polu `parameters.url`.
//
// CZYM TO NIE JEST. To nie jest wyciek. Repo jest czyste, bo `eksport-do-repo.cjs` maskuje
// token i odmawia zapisu, gdy zostanie cos podejrzanego. Token nie byl w historii gita.
// Dlug boli przy ROTACJI: dzis wymiana tokenu to edycja 44 wezlow zamiast jednego wiersza.
//
// ============================================================================
// SFORMULOWANIE MANAGERA (11/08), ktore rzadzi tym plikiem:
//     "Ryzykiem nie jest token, tylko SKRYPT NA 44 WEZLACH."
// HITL Handler to JEDYNY interfejs Tomasza. Zly patch nie psuje bezpieczenstwa - odbiera
// czlowiekowi guziki. Dlatego kazda bramka nizej pada ZAMKNIETA (AP-314): przy liczbie innej
// niz oczekiwana skrypt NIC nie wysyla.
// ============================================================================
//
// DOKAD IDZIE TOKEN. Do `app_secrets`, klucz `telegram_bot_token` - wiersz, ktory JUZ TAM JEST
// i JUZ JEST CZYTANY, w dwoch niezaleznych miejscach:
//   - Scheduler, wezel `Get Keys`  -> `{{ $('Get Keys').first().json.tg }}`  (de-hardkod 02/07),
//   - HITL Handler, wezel `PostgreSQL Lookup Session` -> `... AS tg_token`, a szesc wezlow
//     tego samego workflow uzywa juz `{{ $json.tg_token }}` w adresie.
// Nie wprowadzamy wiec czwartego mechanizmu. Dopisujemy JEDEN wezel do wzorca, ktory w tym
// samym workflow dziala od miesiaca.
//
// DLACZEGO NOWY WEZEL, A NIE `$json.tg_token` WSZEDZIE. Bo `$json` niesie token tylko w tych
// szesciu galeziach, ktore maja wlasny odczyt sekretu. Pozostale 44 wezly leza w galeziach,
// ktore go nie czytaja. Zamiast dopisywac podzapytanie do kilkunastu roznych SQL-i, wstawiamy
// JEDEN wezel `TG Token` bezposrednio za wyzwalaczem:
//
//     Telegram Trigger  ->  TG Token  ->  Detect Update Type  ->  Route By Update Type ...
//
// `Telegram Trigger` ma DOKLADNIE JEDNO wyjscie i prowadzi ono DOKLADNIE do `Detect Update Type`
// (sprawdzone w eksporcie 11/08). Wezel wstawiony w to miejsce jest wiec scisle przed KAZDYM
// z 44 wezlow. To nie jest kwestia wiary w kolejnosc wykonania galezi rownoleglych - to lancuch.
// Galezi rownoleglej celowo NIE uzywamy: przy `executionOrder: v1` kolejnosc galezi zalezy od
// polozenia wezlow na plotnie, a wtedy glebsza galaz moglaby siegnac po `$('TG Token')` zanim
// ten wezel wykonal sie choc raz. Blad bylby losowy, czyli najgorszy z mozliwych.
//
// KOSZT WSTAWKI: jeden wezel `Detect Update Type` przestaje czytac swoje WEJSCIE, bo wejsciem
// bylby teraz wiersz z bazy. Zmieniamy mu jedna linie:
//     const item = items[0].json;                        (dzis)
//     const item = $('Telegram Trigger').first().json;    (po patchu)
// To ta sama dana. Skrypt sprawdza, ze ta linia wystepuje DOKLADNIE RAZ, i liczy podmiane osobno.
//
// UZYCIE - Z MASZYNY TOMASZA, NIE Z SERWERA (na serwerze nie ma `node` ani `.env`).
// Windows PowerShell 5.1 (UWAGA: `&&` w PowerShellu 5.1 NIE ISTNIEJE i daje blad parsera):
//
//   cd C:\Claude-CoWork\AGS\ags-agents
//   Get-Content .\.env | Where-Object { $_ -match '^(N8N_BASE_URL|N8N_API_KEY)=' } | ForEach-Object { $p = $_ -split '=', 2; Set-Item -Path ("Env:" + $p[0].Trim()) -Value $p[1].Trim() }
//   node n8n-workflows\patches\d017-token-bez-hardkodu-19082026.cjs sprawdz
//   node n8n-workflows\patches\d017-token-bez-hardkodu-19082026.cjs sucho
//   node n8n-workflows\patches\d017-token-bez-hardkodu-19082026.cjs zapisz
//   node n8n-workflows\patches\d017-token-bez-hardkodu-19082026.cjs cofnij
//
// Tryb bez sieci, do przetestowania calej przemiany przed oknem (NIE dotyka produkcji):
//   node n8n-workflows\patches\d017-token-bez-hardkodu-19082026.cjs sucho-z-pliku n8n-workflows\x-agent\ags-hitl-handler-v1.json
//
// PAMIETAJ (project_n8n_reactivate_after_put): PUT zapisuje definicje do BAZY, ale AKTYWNY
// snapshot trzyma STARA. Bez `deactivate` + `activate` bot dalej chodzi na wersji sprzed PUT-a,
// a API caly czas odpowiada 200. Ten skrypt robi deactivate+activate SAM i sam porownuje
// `nodes` z `activeVersion`, bo kod odpowiedzi i flaga `active` nie dowodza NICZEGO.
//
// I TAK NA KONIEC POTRZEBNY JEST CZLOWIEK. Dwiescie OK przy martwym webhooku wyglada identycznie
// jak sukces (dowod: okno 19/08, `/health` mowilo `ok`, gdy kazda sciezka LLM byla martwa).
// Dowodem jest WIADOMOSC OD BOTA, nie kod HTTP. Skrypt konczy sie instrukcja, co napisac.

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ID = 'U5pUZjy2yAhR1sWg';
const NAZWA = 'AGS HITL Handler v1.0';

// LICZBY Z ODCZYTU. Policzone 19/08 na eksporcie `n8n-workflows/x-agent/ags-hitl-handler-v1.json`
// (zrzut zywej definicji z 11/08, versionId 1007da15, 254 wezly). Zgadzaja sie z wpisem D-017.
//   44 wezly httpRequest z tokenem w `parameters.url`, po jednym wystapieniu na wezel,
//   z czego 36 ma adres juz jako wyrazenie (prefiks `=`), a 8 jako zwykly napis.
// Osiem "zwyklych" MUSI dostac prefiks `=`, inaczej n8n wstawi klamry doslownie do URL-a.
const OCZEKIWANE_WEZLY = 44;
const OCZEKIWANE_WYRAZENIOWE = 36;
const OCZEKIWANE_ZWYKLE = 8;
const OCZEKIWANE_KOD = 1;

const WEZEL_TOKENU = 'TG Token';
const WYRAZENIE = `{{ $('${WEZEL_TOKENU}').first().json.tg_token }}`;

const TRIGGER = 'Telegram Trigger';
const DETECT = 'Detect Update Type';
const KOD_STARY = 'const item = items[0].json;';
const KOD_NOWY = `const item = $('${TRIGGER}').first().json;`;

// Poswiadczenie Postgresa uzywane przez WSZYSTKIE 69 wezlow postgresowych tego workflow.
const PG_CRED = { postgres: { id: 'aHDeZ1ywfPihvVxH', name: 'PostgreSQL CRD ags-agents' } };

// Adres Telegrama wystepuje w dwoch odmianach: `/bot<TOKEN>/` (API) oraz `/file/bot<TOKEN>/`
// (pobieranie plikow). Ten wzorzec lapie obie. Grupa 2 to wszystko miedzy `bot` a nastepnym
// ukosnikiem, cokolwiek to jest: literal tokenu ALBO wyrazenie w klamrach. Rozroznienie po
// klamrach robi dopiero `skan`, bo skrypt musi umiec policzyc jedno i drugie.
// Pierwsza wersja tego wzorca miala tu `[^/{}]+`, czyli wykluczala klamry - i przez to po
// przemianie widziala zero wezlow "gotowych". Zlapala to kontrola wyniku w trybie na sucho,
// zanim cokolwiek poszlo na produkcje. Zostawiam ten akapit jako dowod, po co ta kontrola jest.
//
// Wzorzec NIE zna tresci tokenu - dziala tak samo na zywym tokenie, jak na zamaskowanym
// `<TELEGRAM_BOT_TOKEN>` z eksportu w repo. Dzieki temu tryb `sucho-z-pliku` testuje DOKLADNIE
// te sama przemiane, ktora pojdzie na produkcje.
const WZOR_URL = /(api\.telegram\.org\/(?:file\/)?bot)([^/]+?)(\/)/;

const ALLOWED = ['saveDataErrorExecution', 'saveDataSuccessExecution', 'saveManualExecutions',
  'saveExecutionProgress', 'executionTimeout', 'errorWorkflow', 'timezone', 'executionOrder',
  'callerPolicy', 'binaryMode'];

const base = process.env.N8N_BASE_URL;
const key = process.env.N8N_API_KEY;
const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };

function wymagajSrodowiska() {
  if (!base || !key) {
    console.error('BRAK N8N_BASE_URL / N8N_API_KEY w srodowisku.');
    console.error('PowerShell 5.1 (jedna linia, w katalogu repo):');
    console.error("  Get-Content .\\.env | Where-Object { $_ -match '^(N8N_BASE_URL|N8N_API_KEY)=' } | ForEach-Object { $p = $_ -split '=', 2; Set-Item -Path (\"Env:\" + $p[0].Trim()) -Value $p[1].Trim() }");
    process.exit(1);
  }
}

async function pobierz() {
  const r = await fetch(`${base}/api/v1/workflows/${ID}`, { headers: H });
  if (!r.ok) { console.error('GET nieudany:', r.status, await r.text()); process.exit(1); }
  return r.json();
}

// ---------------------------------------------------------------------------
// ODCZYT: co siedzi w definicji. Zadnych zmian.
// ---------------------------------------------------------------------------

function skan(w) {
  const twarde = [];      // wezly z literalem tokenu w URL
  const gotowe = [];      // wezly juz przestawione na wyrazenie `TG Token`
  const cudze = [];       // wezly z tokenem z INNEGO wyrazenia (te szesc, ktore juz dzialaja)
  const literaly = new Set();
  let wyrazeniowe = 0, zwykle = 0;

  for (const n of w.nodes || []) {
    const u = n.parameters && n.parameters.url;
    if (typeof u !== 'string') continue;
    const m = u.match(WZOR_URL);
    if (!m) continue;
    const srodek = m[2];
    if (srodek.includes(WYRAZENIE)) { gotowe.push(n.name); continue; }
    if (srodek.includes('{{')) { cudze.push(n.name); continue; }
    twarde.push({ nazwa: n.name, typ: n.type, url: u, wyrazeniowy: u.startsWith('=') });
    literaly.add(srodek);
    if (u.startsWith('=')) wyrazeniowe++; else zwykle++;
  }

  const detect = (w.nodes || []).find((n) => n.name === DETECT);
  const kod = detect && detect.parameters ? String(detect.parameters.jsCode || '') : '';
  const kodStary = kod.split(KOD_STARY).length - 1;
  const kodNowy = kod.split(KOD_NOWY).length - 1;
  const maWezelTokenu = !!(w.nodes || []).find((n) => n.name === WEZEL_TOKENU);

  return { twarde, gotowe, cudze, literaly, wyrazeniowe, zwykle, kodStary, kodNowy, maWezelTokenu, detect };
}

function wypiszSkan(w, s) {
  console.log(`${NAZWA} | aktywny: ${w.active} | wezlow: ${(w.nodes || []).length} | versionId: ${w.versionId || '(brak)'}`);
  console.log('');
  console.log(`  wezlow z tokenem NA SZTYWNO w url : ${s.twarde.length}   (oczekiwane ${OCZEKIWANE_WEZLY})`);
  console.log(`    w tym adres juz jako wyrazenie  : ${s.wyrazeniowe}   (oczekiwane ${OCZEKIWANE_WYRAZENIOWE})`);
  console.log(`    w tym adres jako zwykly napis   : ${s.zwykle}   (oczekiwane ${OCZEKIWANE_ZWYKLE}, kazdy dostanie prefiks "=")`);
  console.log(`  roznych literalow tokenu          : ${s.literaly.size}   (oczekiwany 1)`);
  console.log(`  wezlow juz na "${WEZEL_TOKENU}"          : ${s.gotowe.length}`);
  console.log(`  wezlow z tokenem z innego wyrazenia: ${s.cudze.length}   (te zostawiamy w spokoju: ${s.cudze.join(', ') || 'brak'})`);
  console.log(`  wezel "${WEZEL_TOKENU}" juz istnieje      : ${s.maWezelTokenu ? 'TAK' : 'nie'}`);
  console.log(`  "${DETECT}" linia stara/nowa : ${s.kodStary}/${s.kodNowy}`);
  console.log('');
  console.log('  WEZLY DO PODMIANY:');
  for (const t of s.twarde) console.log(`    ${t.wyrazeniowy ? '=' : ' '} ${t.nazwa}`);
}

// ---------------------------------------------------------------------------
// BRAMKI. Kazda pada ZAMKNIETA: `false` znaczy "nic nie wysylam".
// ---------------------------------------------------------------------------

function bramki(w, s, oczekiwane) {
  const b = [];
  const dodaj = (ok, opis) => b.push({ ok, opis });

  dodaj(s.twarde.length === oczekiwane,
    `liczba wezlow do podmiany: ${s.twarde.length}, oczekiwana ${oczekiwane}`);
  dodaj(s.literaly.size === 1,
    `roznych literalow tokenu: ${s.literaly.size}, oczekiwany dokladnie 1`);
  dodaj(s.wyrazeniowe + s.zwykle === s.twarde.length,
    `rozklad wyrazeniowe/zwykle sumuje sie: ${s.wyrazeniowe}+${s.zwykle}=${s.twarde.length}`);
  dodaj(s.maWezelTokenu === false,
    `wezel "${WEZEL_TOKENU}" jeszcze nie istnieje (patch nie jest juz zalozony)`);
  dodaj(!!s.detect, `wezel "${DETECT}" istnieje`);
  dodaj(s.kodStary === OCZEKIWANE_KOD,
    `"${DETECT}": linia "${KOD_STARY}" wystepuje ${s.kodStary} raz, oczekiwane ${OCZEKIWANE_KOD}`);
  const wyj = w.connections && w.connections[TRIGGER] && w.connections[TRIGGER].main;
  const ksztalt = JSON.stringify((wyj || []).map((g) => (g || []).map((x) => x.node)));
  dodaj(ksztalt === JSON.stringify([[DETECT]]),
    `wyjscie "${TRIGGER}" ma ksztalt [["${DETECT}"]], jest ${ksztalt}`);
  dodaj(s.gotowe.length === 0,
    `zero wezlow juz przestawionych na "${WEZEL_TOKENU}" (jest ${s.gotowe.length})`);
  return b;
}

function wypiszBramki(b) {
  console.log('  BRAMKI (kazda musi byc OK, inaczej nic nie leci na produkcje):');
  for (const x of b) console.log(`    ${x.ok ? 'OK  ' : 'STOP'}  ${x.opis}`);
  const zle = b.filter((x) => !x.ok);
  console.log('');
  if (zle.length) {
    console.log(`  BRAMKA ZAMKNIETA: ${zle.length} z ${b.length} warunkow niespelnionych.`);
    console.log('  NIE zgaduj i NIE podnos oczekiwanej liczby "na oko". Jesli zywa definicja');
    console.log('  urosla albo zmalala od 11/08, to jest USTALENIE (AP-316) - zglos je i dopiero');
    console.log('  potem odpal z jawna liczba: ... zapisz --oczekiwane=N');
  }
  return zle.length === 0;
}

// ---------------------------------------------------------------------------
// PRZEMIANA. Wykonywana zawsze NA KOPII, w pamieci, przed jakimkolwiek zapisem.
// ---------------------------------------------------------------------------

function przemien(w) {
  const kopia = JSON.parse(JSON.stringify(w));
  let url = 0, prefiks = 0;

  for (const n of kopia.nodes) {
    const u = n.parameters && n.parameters.url;
    if (typeof u !== 'string') continue;
    const m = u.match(WZOR_URL);
    if (!m || m[2].includes('{{')) continue;
    let nowy = u.replace(WZOR_URL, `$1${WYRAZENIE}$3`);
    if (!nowy.startsWith('=')) { nowy = '=' + nowy; prefiks++; }
    n.parameters.url = nowy;
    url++;
  }

  const detect = kopia.nodes.find((n) => n.name === DETECT);
  const kodPrzed = String(detect.parameters.jsCode || '');
  detect.parameters.jsCode = kodPrzed.split(KOD_STARY).join(KOD_NOWY);
  const kod = kodPrzed.split(KOD_STARY).length - 1;

  // Wezel czytajacy sekret. Ten sam ksztalt, co `Plannav Secret` i pozostale odczyty
  // `app_secrets` w tym workflow: postgres 2.4, `executeQuery`, to samo poswiadczenie.
  kopia.nodes.push({
    id: crypto.randomUUID(),
    name: WEZEL_TOKENU,
    type: 'n8n-nodes-base.postgres',
    typeVersion: 2.4,
    position: [-104, 160],
    parameters: {
      operation: 'executeQuery',
      query: "SELECT value AS tg_token FROM app_secrets WHERE key='telegram_bot_token' LIMIT 1;",
      options: {},
    },
    credentials: PG_CRED,
  });

  // Lancuch: Trigger -> TG Token -> Detect. Nie galaz rownolegla (patrz naglowek pliku).
  kopia.connections[TRIGGER] = { main: [[{ node: WEZEL_TOKENU, type: 'main', index: 0 }]] };
  kopia.connections[WEZEL_TOKENU] = { main: [[{ node: DETECT, type: 'main', index: 0 }]] };

  return { kopia, url, prefiks, kod };
}

function skontroluj(przed, po, oczekiwane, zmiany) {
  const s = skan(po);
  const k = [];
  const dodaj = (ok, opis) => k.push({ ok, opis });

  dodaj(zmiany.url === oczekiwane, `podmieniono ${zmiany.url} adresow, oczekiwane ${oczekiwane}`);
  dodaj(zmiany.prefiks === OCZEKIWANE_ZWYKLE,
    `prefiks "=" dopisano ${zmiany.prefiks} razy, oczekiwane ${OCZEKIWANE_ZWYKLE}`);
  dodaj(zmiany.kod === OCZEKIWANE_KOD, `linie kodu podmieniono ${zmiany.kod} raz, oczekiwane ${OCZEKIWANE_KOD}`);
  dodaj(s.twarde.length === 0, `literalow tokenu po przemianie: ${s.twarde.length}, ma byc 0`);
  dodaj(s.gotowe.length === oczekiwane,
    `wezlow na "${WEZEL_TOKENU}" po przemianie: ${s.gotowe.length}, ma byc ${oczekiwane}`);
  // Wezly, ktore JUZ czytaly token z wlasnego wyrazenia (odczyt 19/08: szesc), maja przejsc
  // patch nietkniete. Porownujemy ze stanem SPRZED, a nie z zapisana na sztywno szostka:
  // gdyby ktos w miedzyczasie naprawil siodmy recznie, bramka ma to przepuscic, a nie zatrzymac.
  const cudzePrzed = skan(przed).cudze.length;
  dodaj(s.cudze.length === cudzePrzed,
    `wezlow z wlasnym wyrazeniem tokenu bez zmian: ${cudzePrzed} -> ${s.cudze.length}`);
  dodaj(s.kodStary === 0 && s.kodNowy === OCZEKIWANE_KOD,
    `"${DETECT}": stara linia ${s.kodStary} (ma byc 0), nowa ${s.kodNowy} (ma byc ${OCZEKIWANE_KOD})`);
  dodaj(po.nodes.length === przed.nodes.length + 1,
    `wezlow: ${przed.nodes.length} -> ${po.nodes.length} (dokladnie jeden wiecej)`);
  const l1 = JSON.stringify(po.connections[TRIGGER].main.map((g) => g.map((x) => x.node)));
  const l2 = JSON.stringify(po.connections[WEZEL_TOKENU].main.map((g) => g.map((x) => x.node)));
  dodaj(l1 === JSON.stringify([[WEZEL_TOKENU]]) && l2 === JSON.stringify([[DETECT]]),
    `lancuch ${TRIGGER} -> ${WEZEL_TOKENU} -> ${DETECT}: ${l1} ${l2}`);

  // Poza tym patch NIE MA prawa niczego ruszyc. Porownanie calej reszty definicji, wezel po
  // wezle: rozne moga byc wylacznie 44 adresy, jedna linia kodu i jeden nowy wezel.
  const mapa = (x) => new Map(x.nodes.map((n) => [n.name, JSON.stringify(n)]));
  const mp = mapa(przed), mo = mapa(po);
  let inne = 0;
  for (const [nazwa, tresc] of mp) if (mo.get(nazwa) !== tresc) inne++;
  dodaj(inne === oczekiwane + OCZEKIWANE_KOD,
    `zmienionych wezlow lacznie: ${inne}, oczekiwane ${oczekiwane + OCZEKIWANE_KOD} (adresy plus "${DETECT}")`);

  return k;
}

// ---------------------------------------------------------------------------
// TRYBY
// ---------------------------------------------------------------------------

function oczekiwaneZArgumentow() {
  const a = process.argv.find((x) => x.startsWith('--oczekiwane='));
  if (!a) return OCZEKIWANE_WEZLY;
  const n = parseInt(a.split('=')[1], 10);
  if (!Number.isInteger(n) || n <= 0) { console.error('Zla wartosc --oczekiwane=', a); process.exit(1); }
  console.log(`UWAGA: oczekiwana liczba podniesiona recznie z ${OCZEKIWANE_WEZLY} na ${n}.`);
  console.log('Wolno tego uzyc TYLKO po przebiegu `sucho` i po zgloszeniu roznicy koordynatorowi.');
  return n;
}

async function sprawdz() {
  wymagajSrodowiska();
  const w = await pobierz();
  const s = skan(w);
  wypiszSkan(w, s);
  console.log('');
  wypiszBramki(bramki(w, s, oczekiwaneZArgumentow()));
  console.log('To byl czysty odczyt. Nic nie wyslano.');
  process.exit(0);
}

async function sucho(zPliku) {
  let w;
  if (zPliku) {
    const p = path.resolve(zPliku);
    console.log('PRZEBIEG BEZ SIECI, na pliku:', p);
    console.log('Produkcja NIE zostala dotknieta.');
    console.log('');
    w = JSON.parse(fs.readFileSync(p, 'utf8'));
  } else {
    wymagajSrodowiska();
    console.log('PRZEBIEG NA SUCHO na ZYWEJ definicji. Tylko GET - nic nie zapisuje.');
    console.log('');
    w = await pobierz();
  }

  const s = skan(w);
  wypiszSkan(w, s);
  console.log('');
  const oczekiwane = oczekiwaneZArgumentow();
  const otwarte = wypiszBramki(bramki(w, s, oczekiwane));
  if (!otwarte) { console.log('KONIEC: bramka zamknieta, przemiany nawet nie probuje.'); process.exit(1); }

  const { kopia, url, prefiks, kod } = przemien(w);
  console.log('  PRZEMIANA W PAMIECI:');
  console.log(`    adresow podmienionych : ${url}`);
  console.log(`    prefiksow "=" dopisanych: ${prefiks}`);
  console.log(`    linii kodu podmienionych: ${kod}`);
  console.log('');
  const k = skontroluj(w, kopia, oczekiwane, { url, prefiks, kod });
  console.log('  KONTROLA WYNIKU:');
  for (const x of k) console.log(`    ${x.ok ? 'OK  ' : 'STOP'}  ${x.opis}`);
  const dobrze = k.every((x) => x.ok);
  console.log('');
  console.log('  PRZYKLAD adresu po przemianie:');
  const p1 = kopia.nodes.find((n) => n.name === s.twarde[0].nazwa);
  console.log(`    ${s.twarde[0].nazwa}`);
  console.log(`      przed: ${s.twarde[0].url}`);
  console.log(`      po   : ${p1.parameters.url}`);
  console.log('');
  console.log(dobrze
    ? 'WYNIK: przemiana przechodzi. Mozna isc do trybu `zapisz` (ten dopiero wysyla PUT).'
    : 'WYNIK: przemiana NIE przechodzi. Do trybu `zapisz` NIE WOLNO isc.');
  process.exit(dobrze ? 0 : 1);
}

async function zapisz() {
  wymagajSrodowiska();
  const oczekiwane = oczekiwaneZArgumentow();
  const w = await pobierz();
  const s = skan(w);
  wypiszSkan(w, s);
  console.log('');
  if (!wypiszBramki(bramki(w, s, oczekiwane))) { console.log('NIC NIE WYSLANO.'); process.exit(1); }

  // KOPIA PRZED PUT-em. Bezwarunkowo i przed czymkolwiek innym (wymog 1 Managera).
  // Plik lapie sie na regule `.gitignore` na `bk_*.json` i zawiera ZYWY token - nie commitowac.
  const kopiaPlik = path.join(__dirname, `bk_hitl_d017_${Date.now()}.json`);
  fs.writeFileSync(kopiaPlik, JSON.stringify(w, null, 2));
  const rozmiar = fs.statSync(kopiaPlik).size;
  console.log(`  KOPIA DEFINICJI: ${kopiaPlik}  (${(rozmiar / 1024).toFixed(0)} KB)`);
  const odczytana = JSON.parse(fs.readFileSync(kopiaPlik, 'utf8'));
  if (!odczytana.nodes || odczytana.nodes.length !== w.nodes.length) {
    console.error('STOP: kopia zapasowa nie daje sie odczytac albo ma inna liczbe wezlow.');
    console.error('Kopia, ktora TWIERDZI, ze istnieje, jest gorsza niz jej brak. Nic nie wysylam.');
    process.exit(1);
  }
  console.log(`  kopia odczytana z powrotem: ${odczytana.nodes.length} wezlow. OK.`);
  console.log('');

  const { kopia, url, prefiks, kod } = przemien(w);
  const k = skontroluj(w, kopia, oczekiwane, { url, prefiks, kod });
  console.log('  KONTROLA PRZED WYSLANIEM:');
  for (const x of k) console.log(`    ${x.ok ? 'OK  ' : 'STOP'}  ${x.opis}`);
  if (!k.every((x) => x.ok)) {
    console.error('\nSTOP: przemiana nie zgadza sie z oczekiwaniem. NIC NIE WYSLANO.');
    console.error('Definicja zostala nietknieta. Kopia lezy w:', kopiaPlik);
    process.exit(1);
  }
  console.log('');

  await wyslij(kopia, oczekiwane, false, kopiaPlik);
}

async function cofnij() {
  wymagajSrodowiska();
  let plik = process.argv[3];
  if (!plik || plik.startsWith('--')) {
    const lista = fs.readdirSync(__dirname)
      .filter((f) => /^bk_hitl_d017_\d+\.json$/.test(f))
      .sort()
      .reverse();
    if (!lista.length) {
      console.error('STOP: nie podano pliku kopii i nie znalazlem zadnego bk_hitl_d017_*.json.');
      console.error('Uzycie: ... cofnij <sciezka-do-kopii.json>');
      process.exit(1);
    }
    plik = path.join(__dirname, lista[0]);
    console.log('Kopii nie podano. Biore NAJNOWSZA:', plik);
  }
  const stara = JSON.parse(fs.readFileSync(path.resolve(plik), 'utf8'));
  const s = skan(stara);
  console.log(`KOPIA: ${stara.nodes.length} wezlow | literalow tokenu: ${s.twarde.length} | wezel "${WEZEL_TOKENU}": ${s.maWezelTokenu ? 'jest' : 'brak'}`);
  if (s.twarde.length === 0 && s.maWezelTokenu) {
    console.error('STOP: ta kopia jest JUZ PO patchu, nie sprzed. Cofniecie do niej nic nie cofnie.');
    process.exit(1);
  }
  if (!stara.nodes || !stara.connections) {
    console.error('STOP: plik kopii nie wyglada na definicje workflow.');
    process.exit(1);
  }
  console.log('');
  await wyslij(stara, s.twarde.length, true, plik);
}

// ---------------------------------------------------------------------------
// WYSYLKA. deactivate -> PUT -> GET -> activate -> GET -> porownanie z activeVersion.
// ---------------------------------------------------------------------------

async function wyslij(def, oczekiwane, cofamy, kopiaPlik) {
  console.log('  Od tej chwili guziki w bocie nie odpowiadaja. Okno liczy sie w sekundach.');
  const de = await fetch(`${base}/api/v1/workflows/${ID}/deactivate`, { method: 'POST', headers: H });
  console.log('  deactivate:', de.status);

  const settings = {};
  for (const kk of ALLOWED) if (def.settings && def.settings[kk] !== undefined) settings[kk] = def.settings[kk];
  const put = await fetch(`${base}/api/v1/workflows/${ID}`, {
    method: 'PUT', headers: H,
    body: JSON.stringify({ name: def.name, nodes: def.nodes, connections: def.connections, settings }),
  });
  console.log('  PUT:', put.status);
  if (put.status !== 200) {
    console.error(await put.text());
    console.error('  PRZYWRACAM AKTYWNOSC, zeby nie zostawic Tomasza bez guzikow.');
    const r = await fetch(`${base}/api/v1/workflows/${ID}/activate`, { method: 'POST', headers: H });
    console.error('  activate:', r.status);
    console.error('  Definicja w bazie powinna byc nietknieta. Kopia:', kopiaPlik);
    process.exit(1);
  }

  // 200 znaczy "przyjalem", nie "zapisalem to, co myslisz".
  const poPut = await pobierz();
  const sp = skan(poPut);
  console.log(`  po PUT (baza): literaly ${sp.twarde.length} | na "${WEZEL_TOKENU}" ${sp.gotowe.length} | wezlow ${poPut.nodes.length}`);

  const ak = await fetch(`${base}/api/v1/workflows/${ID}/activate`, { method: 'POST', headers: H });
  console.log('  activate:', ak.status);

  const kon = await pobierz();
  console.log('  flaga active:', kon.active);
  console.log('');

  // TO JEST TA WLASCIWA KONTROLA. `nodes` to definicja w bazie, `activeVersion` to migawka
  // WERSJI URUCHOMIONEJ. Przy D-016 dopiero to porownanie pokazalo, czy bot chodzi na nowym.
  // Brak `activeVersion` NIE jest sukcesem - jest brakiem dowodu (AP-317).
  let dowod = false;
  if (!kon.activeVersion) {
    console.log('  activeVersion: BRAK w odpowiedzi API.');
    console.log('  NIE UMIEM POTWIERDZIC, ze bot chodzi na nowej definicji. To nie jest sukces.');
    console.log('  Dowod musi wtedy dac WYLACZNIE zachowanie bota (sekcja nizej).');
  } else {
    const tekstAV = JSON.stringify(kon.activeVersion);
    const wAV = tekstAV.split(WYRAZENIE).length - 1;
    // Ile literalow zostalo w migawce: liczymy adresy Telegrama bez klamer.
    const literalyAV = (tekstAV.match(/api\.telegram\.org\/(?:file\/)?bot(?!\{\{)[^/]+?\//g) || []).length;
    const wNodes = JSON.stringify(kon.nodes).split(WYRAZENIE).length - 1;
    console.log(`  nodes         : wyrazenie "${WEZEL_TOKENU}" x${wNodes}`);
    console.log(`  activeVersion : wyrazenie x${wAV} | adresow z literalem x${literalyAV}`);
    dowod = cofamy ? (wAV === 0 && literalyAV === oczekiwane) : (wAV === wNodes && wAV === oczekiwane && literalyAV === 0);
    console.log(dowod
      ? '  ZGODNE: uruchomiona wersja to ta, ktora wlasnie zapisalem.'
      : '  NIEZGODNE: uruchomiona wersja to NIE jest ta, ktora zapisalem. Cofnij patch.');
  }

  const zapisOk = cofamy
    ? (sp.twarde.length === oczekiwane && sp.gotowe.length === 0)
    : (sp.twarde.length === 0 && sp.gotowe.length === oczekiwane);
  console.log('');
  console.log(zapisOk ? '  ZAPIS: definicja w bazie zgodna z zamiarem.' : '  ZAPIS: definicja w bazie NIE zgadza sie z zamiarem.');
  console.log(kon.active ? '  STAN: workflow aktywny.' : '  STAN: workflow NIEAKTYWNY - wlacz recznie w n8n, Tomasz nie ma guzikow!');
  console.log('');
  console.log('  ================================================================');
  console.log('  DOWOD KONCOWY DAJE CZLOWIEK, NIE TEN SKRYPT.');
  console.log('  Dwiescie OK przy martwym webhooku wyglada identycznie jak sukces.');
  if (cofamy) {
    console.log('  Napisz do bota na Telegramie:  /menu');
    console.log('  Ma przyjsc menu z guzikami. Cofniecie, ktorego nie sprawdziles wiadomoscia,');
    console.log('  nie jest cofnieciem. Jesli bot MILCZY, wejdz w panel n8n i sprawdz recznie,');
    console.log(`  czy "${NAZWA}" jest aktywny.`);
  } else {
    console.log('  Cztery proby, kazda dotyka innej grupy z tych 44 wezlow (krok 5 procedury');
    console.log('  docs/ops/OKNO_D017_przygotowane.md):');
    console.log('    1. /menu                          -> ma przyjsc menu z guzikami');
    console.log('    2. tapnij guzik w tym menu        -> guzik przestaje sie krecic od razu');
    console.log('    3. zwykly tekst, np. "proba D-017" -> ma przyjsc karta podgladu pomyslu');
    console.log('    4. wyslij dowolne zdjecie         -> ma przyjsc normalna reakcja');
    console.log('  CISZA na ktorejkolwiek probie = token nie dziala. Wtedy natychmiast:');
    console.log(`     node n8n-workflows\\patches\\d017-token-bez-hardkodu-19082026.cjs cofnij "${kopiaPlik}"`);
  }
  console.log('  ================================================================');
  process.exit(zapisOk && kon.active ? 0 : 1);
}

const tryb = (process.argv[2] || '').toLowerCase();
const tryby = {
  sprawdz,
  sucho: () => sucho(null),
  'sucho-z-pliku': () => sucho(process.argv[3]),
  zapisz,
  cofnij,
};
if (!tryby[tryb]) {
  console.log('Tryby:');
  console.log('  sprawdz                     odczyt zywej definicji plus bramki, bez przemiany');
  console.log('  sucho                       przebieg na sucho na ZYWEJ definicji (tylko GET)');
  console.log('  sucho-z-pliku <plik.json>   przebieg na sucho BEZ SIECI, na eksporcie z repo');
  console.log('  zapisz [--oczekiwane=N]     kopia, bramki, PUT, deactivate+activate, kontrola');
  console.log('  cofnij [plik-kopii.json]    powrot do definicji sprzed patcha');
  console.log('');
  console.log('Zawsze w tej kolejnosci: sucho-z-pliku, potem sucho, dopiero potem zapisz.');
  process.exit(1);
}
tryby[tryb]().catch((e) => { console.error('BLAD:', e.message); process.exit(1); });
