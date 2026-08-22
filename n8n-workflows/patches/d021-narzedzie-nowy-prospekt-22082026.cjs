// D-021 (22/08/2026): rejestracja narzedzia `nowy_prospekt` w workflow `AGS Lacznik Chat Tools`.
//
// PO CO. Kod cm-agenta wystawia `POST /lacznik/nowy-prospekt` od 19/08 i dziala, ale Manager
// NADAL nie ma jak zalozyc prospekta, bo narzedzia nie ma w rozmowie. To jest AP-307 co do
// litery: nowy kontrakt zbudowany bez przelaczenia zywego konsumenta wyglada na cala robote,
// a jest polowa. Ten skrypt domyka druga polowe.
//
// DLACZEGO SKRYPT, A NIE RECZNA EDYCJA W UI. Osiem nazw `$fromAI` to KONTRAKT widziany przez
// wolajacego. Pomylka w jednej z nich daje `Received tool input did not match expected schema`
// (pulapka zlapana tap-testem 31/07: wezel mial `contact_id`, a Manager wolal `kontakt`).
// Do tego `typeVersion` musi byc 4.2, bo kopiowanie z dokumentacji zamiast z dzialajacego
// wezla to AP-301. Reka tego nie zrobi powtarzalnie, skrypt tak.
//
// SEKRET: skrypt PRZEJMUJE go z ZYWEJ definicji, z istniejacego wezla `teczka`. Nie podaje sie
// go z zewnatrz i nie czyta z repo. Powod podwojny: (1) sekret siedzi tez w sciezce triggera
// MCP, wiec jakakolwiek jego zmiana rozjezdza adres konektora w claude.ai; (2) eksport w repo
// zawiera go otwartym tekstem i to jest osobny dlug D-026 - nie chcemy go tu utrwalac.
//
// UZYCIE - z maszyny Tomasza, nie z serwera (na Mikrusie nie ma `node` ani `.env`).
// PowerShell 5.1 (`&&` NIE ISTNIEJE w tej powloce, dlatego `;` i `if ($?)`):
//
//   cd C:\Claude-CoWork\AGS\ags-agents
//   Get-Content .\.env | Where-Object { $_ -match '^(N8N_BASE_URL|N8N_API_KEY)=' } | ForEach-Object { $p = $_ -split '=', 2; Set-Item -Path ("Env:" + $p[0].Trim()) -Value $p[1].Trim() }
//   node n8n-workflows\patches\d021-narzedzie-nowy-prospekt-22082026.cjs sprawdz
//   node n8n-workflows\patches\d021-narzedzie-nowy-prospekt-22082026.cjs zapisz
//   node n8n-workflows\patches\d021-narzedzie-nowy-prospekt-22082026.cjs cofnij
//
// PO KAZDYM PUT: deactivate + activate. PUT zapisuje do bazy, ale AKTYWNY snapshot trzyma
// STARA definicje - narzedzie byloby w bazie i nie byloby go w rozmowie. Skrypt robi to sam.

const fs = require('fs');
const path = require('path');

const ID = 'yxJUJmZpSUe0tw9K';
const NAZWA = 'nowy_prospekt';
const WZORZEC = 'teczka';        // z niego przejmujemy sekret i ksztalt
const MCP = 'MCP Lacznik';
const OCZEKIWANE_PRZED = 4;      // tyle narzedzi ma byc PRZED zmiana
const OCZEKIWANE_PO = 5;

const base = process.env.N8N_BASE_URL;
const key = process.env.N8N_API_KEY;
const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };

function wymagajSrodowiska() {
  if (!base || !key) {
    console.error('BRAK N8N_BASE_URL / N8N_API_KEY w srodowisku.');
    console.error('PowerShell 5.1, jedna linia, w katalogu repo:');
    console.error("  Get-Content .\\.env | Where-Object { $_ -match '^(N8N_BASE_URL|N8N_API_KEY)=' } | ForEach-Object { $p = $_ -split '=', 2; Set-Item -Path (\"Env:\" + $p[0].Trim()) -Value $p[1].Trim() }");
    process.exit(1);
  }
}

async function pobierz() {
  const r = await fetch(`${base}/api/v1/workflows/${ID}`, { headers: H });
  if (!r.ok) { console.error('GET nieudany:', r.status, await r.text()); process.exit(1); }
  return r.json();
}

const OPIS = [
  'Zaklada NOWEGO prospekta w lejku sprzedazowym AGS. Wolaj, gdy pojawia sie podmiot albo',
  'osoba, ktorej w lejku jeszcze nie ma - to JEDYNA droga zalozenia wiersza; zapisz_tekst',
  'swiadomie odmawia i tak ma zostac. Bramka duplikatow patrzy na PARE domena plus oddzial,',
  'wiec dwa oddzialy tej samej franczyzy przechodza jako dwa osobne prospekty. Jesli bramka',
  'odmowi, dostaniesz nazwe i identyfikator wiersza, ktory uznala za ten sam, oraz liste',
  'danych, ktore przepadna - NIE porzucaj ich, tylko dopisz je przez pipeline_move do tamtego',
  'wiersza. Jesli to naprawde inny podmiot, zawolaj ponownie i wypelnij pole oddzial. UWAGA:',
  'n8n wymaga wszystkich parametrow, wiec dla tych, ktore nie dotycza, podaj PUSTY CIAG -',
  'system potraktuje je jak brak.',
].join(' ');

// Nazwy kluczy `$fromAI` sa KONTRAKTEM widzianym przez wolajacego. Nie zmieniac bez tap-testu.
const POLA = [
  ['nazwa', 'Pelna nazwa podmiotu albo imie i nazwisko osoby, tak jak ma stac w lejku'],
  ['url', 'Adres strony prospekta. PUSTY CIAG jesli nie znasz - nie zgaduj domeny'],
  ['oddzial', 'Miasto oddzialu albo nazwisko, ktore odroznia ten podmiot od innego o tej samej domenie (franczyza: Egurrola Katowice kontra Egurrola Grodzisk). Zapisze sie jako wartosc ZAOBSERWOWANA, wiec podawaj TYLKO to, co wiesz. PUSTY CIAG jesli nie wiesz'],
  ['osoba', 'Osoba do kontaktu albo dojscie, np. przez Piotra Hamryszaka. PUSTY CIAG jesli nie dotyczy'],
  ['email', 'Adres mailowy prospekta. PUSTY CIAG jesli nie masz'],
  ['telefon', 'Telefon prospekta. PUSTY CIAG jesli nie masz'],
  ['notatka', 'Pierwsza linia kartoteki: czym sie zajmuja i skad sie wzieli, np. Szkola tanca, Katowice. Kontakt pierwszego stopnia na LinkedInie. PUSTY CIAG jesli nie dotyczy'],
  ['etap', 'Etap lejka: prospect, qualified, proposal, negotiation, won, lost albo parked. PUSTY CIAG oznacza prospect'],
];

function cialo() {
  const pary = POLA.map(([k, o]) => `${k}: $fromAI('${k}', '${o.replace(/'/g, "\\'")}', 'string')`);
  return `={{ JSON.stringify({ ${pary.join(', ')} }) }}`;
}

function narzedzia(w) {
  return (w.nodes || []).filter(n => n.type === 'n8n-nodes-base.httpRequestTool');
}

function sekretZZywej(w) {
  const wz = (w.nodes || []).find(n => n.name === WZORZEC);
  if (!wz) return null;
  const p = ((wz.parameters || {}).headerParameters || {}).parameters || [];
  const h = p.find(x => (x.name || '').toLowerCase() === 'x-lacznik-secret');
  return h ? h.value : null;
}

// --- BRAMKI. Kazda pada ZAMKNIETA: brak pewnosci = STOP, nie "pewnie ok" (AP-314). ---
function bramki(w) {
  const t = narzedzia(w);
  const sek = sekretZZywej(w);
  const wz = (w.nodes || []).find(n => n.name === WZORZEC);
  const lista = [
    [t.length === OCZEKIWANE_PRZED, `narzedzi przed zmiana: ${t.length}, oczekiwane ${OCZEKIWANE_PRZED}`],
    [!(w.nodes || []).some(n => n.name === NAZWA), `wezel "${NAZWA}" jeszcze nie istnieje (patch nie jest juz zalozony)`],
    [!!wz, `wezel wzorcowy "${WZORZEC}" istnieje`],
    [!!sek && sek.length >= 16, `sekret przejety z zywej definicji (dlugosc ${sek ? sek.length : 0}, ma byc >= 16)`],
    [!!(w.connections || {})[WZORZEC], `wzorzec "${WZORZEC}" ma wpis w connections do skopiowania`],
    [(w.nodes || []).some(n => n.name === MCP), `wezel "${MCP}" istnieje`],
  ];
  let ok = true;
  for (const [w2, opis] of lista) {
    console.log(`    ${w2 ? 'OK  ' : 'STOP'}  ${opis}`);
    if (!w2) ok = false;
  }
  return ok;
}

function dodajWezel(w) {
  const wz = (w.nodes || []).find(n => n.name === WZORZEC);
  const sek = sekretZZywej(w);
  const poz = Array.isArray(wz.position) ? [wz.position[0], (wz.position[1] || 0) + 180] : [900, 440];
  const nowy = {
    name: NAZWA,
    type: 'n8n-nodes-base.httpRequestTool',
    typeVersion: 4.2,          // AP-301: kopiowane z DZIALAJACEGO wezla, nie z dokumentacji
    position: poz,
    parameters: {
      toolDescription: OPIS,
      method: 'POST',
      url: 'http://cm-agent:8089/lacznik/nowy-prospekt',
      sendHeaders: true,
      headerParameters: { parameters: [{ name: 'X-Lacznik-Secret', value: sek }] },
      sendBody: true,
      specifyBody: 'json',
      jsonBody: cialo(),
      // neverError OBOWIAZKOWE: odmowa bramki wraca jako HTTP 400 z trescia DLA CZLOWIEKA
      // (ktory wiersz uznano za ten sam, co przepadnie). Bez tego czat zobaczy "tool call
      // failed" i cala robota bramki zniknie.
      options: { response: { response: { neverError: true } } },
    },
  };
  w.nodes.push(nowy);
  w.connections = w.connections || {};
  w.connections[NAZWA] = { ai_tool: [[{ node: MCP, type: 'ai_tool', index: 0 }]] };
  return w;
}

function kontrolaPo(w) {
  const t = narzedzia(w);
  const n = (w.nodes || []).find(x => x.name === NAZWA);
  const jb = n ? (n.parameters || {}).jsonBody || '' : '';
  const brakujace = POLA.map(([k]) => k).filter(k => !jb.includes(`$fromAI('${k}'`));
  const lista = [
    [t.length === OCZEKIWANE_PO, `narzedzi po zmianie: ${t.length}, ma byc ${OCZEKIWANE_PO}`],
    [!!n, `wezel "${NAZWA}" istnieje`],
    [n && n.typeVersion === 4.2, `typeVersion = 4.2 (AP-301)`],
    [brakujace.length === 0, `wszystkie osiem nazw $fromAI obecne${brakujace.length ? ' - BRAK: ' + brakujace.join(', ') : ''}`],
    [!!(((n || {}).parameters || {}).options || {}).response, `neverError ustawione (odmowa bramki ma dojsc jako TRESC)`],
    [!!(w.connections || {})[NAZWA], `polaczenie ai_tool do "${MCP}" dopisane`],
  ];
  let ok = true;
  for (const [w2, opis] of lista) {
    console.log(`    ${w2 ? 'OK  ' : 'STOP'}  ${opis}`);
    if (!w2) ok = false;
  }
  return ok;
}

function doWyslania(w) {
  return { name: w.name, nodes: w.nodes, connections: w.connections, settings: w.settings || {} };
}

async function przelacz() {
  // PUT zapisuje do bazy, ale aktywny snapshot trzyma STARA definicje.
  await fetch(`${base}/api/v1/workflows/${ID}/deactivate`, { method: 'POST', headers: H });
  const r = await fetch(`${base}/api/v1/workflows/${ID}/activate`, { method: 'POST', headers: H });
  return r.ok;
}

(async () => {
  const tryb = (process.argv[2] || '').toLowerCase();
  wymagajSrodowiska();

  if (tryb === 'sprawdz') {
    const w = await pobierz();
    console.log(`Workflow: ${w.name} | wezlow: ${(w.nodes || []).length} | aktywny: ${w.active}`);
    console.log('  NARZEDZIA:', narzedzia(w).map(n => n.name).join(', '));
    console.log('\n  BRAMKI:');
    const ok = bramki(w);
    if (!ok) { console.log('\nKONIEC: bramka zamknieta, nic nie wysylam.'); process.exit(1); }
    console.log('\n  PROBA W PAMIECI (nic nie wyslano):');
    kontrolaPo(dodajWezel(JSON.parse(JSON.stringify(w))));
    console.log('\nWYNIK: mozna isc do trybu `zapisz`.');
    process.exit(0);
  }

  if (tryb === 'zapisz') {
    const w = await pobierz();
    const kopiaPlik = path.resolve(`bk_lacznik_d021_${Date.now()}.json`);
    fs.writeFileSync(kopiaPlik, JSON.stringify(w, null, 1));
    console.log('KOPIA PRZED ZMIANA:', kopiaPlik);
    console.log('  UWAGA: ta kopia zawiera ZYWY sekret. NIE commituj jej (D-026).');
    console.log('\n  BRAMKI:');
    if (!bramki(w)) { console.log('\nNIC NIE WYSLANO.'); process.exit(1); }
    const nowy = dodajWezel(JSON.parse(JSON.stringify(w)));
    console.log('\n  KONTROLA PRZED WYSLANIEM:');
    if (!kontrolaPo(nowy)) { console.log('\nNIC NIE WYSLANO.'); process.exit(1); }

    const r = await fetch(`${base}/api/v1/workflows/${ID}`, {
      method: 'PUT', headers: H, body: JSON.stringify(doWyslania(nowy)),
    });
    if (!r.ok) { console.error('PUT nieudany:', r.status, await r.text()); process.exit(1); }
    console.log('\nPUT OK. Przelaczam deactivate + activate...');
    const akt = await przelacz();

    // 200 i flaga active NIE DOWODZA NICZEGO - czytamy definicje z powrotem.
    const po = await pobierz();
    console.log('\n  DOWOD Z ODCZYTU:');
    const dobrze = kontrolaPo(po);
    console.log(`    ${akt && po.active ? 'OK  ' : 'STOP'}  workflow aktywny po przelaczeniu: ${po.active}`);
    console.log('\nTERAZ TAP-TEST NA ZYWYM (bez niego dlug NIE jest zamkniety):');
    console.log('  1. Zaloz: nazwa "Rafal Petrykowski", osoba "Rafal Petrykowski",');
    console.log('     notatka "Kontakt pierwszego stopnia na LinkedInie, rozmowe odwrocil Tomasz".');
    console.log('     Oczekiwane: potwierdzenie z identyfikatorem nowego wiersza.');
    console.log('  2. To samo wolanie DRUGI raz. Oczekiwane: ODMOWA z nazwa i identyfikatorem');
    console.log('     wiersza z punktu 1. Jesli wiersz doszedl drugi raz - bramka nie dziala.');
    console.log('  3. Franczyza: nazwa "Katowice Egurrola Dance Studio", url "https://egurrola.com".');
    console.log('     Oczekiwane: PRZECHODZI, mimo ze Grodzisk stoi na tej samej domenie.');
    process.exit(dobrze && akt && po.active ? 0 : 1);
  }

  if (tryb === 'cofnij') {
    const plik = process.argv[3];
    if (!plik) { console.error('Podaj plik kopii: cofnij bk_lacznik_d021_<...>.json'); process.exit(1); }
    const w = JSON.parse(fs.readFileSync(path.resolve(plik), 'utf8'));
    const r = await fetch(`${base}/api/v1/workflows/${ID}`, {
      method: 'PUT', headers: H, body: JSON.stringify(doWyslania(w)),
    });
    if (!r.ok) { console.error('PUT nieudany:', r.status, await r.text()); process.exit(1); }
    await przelacz();
    const po = await pobierz();
    console.log('COFNIETE. Narzedzia:', narzedzia(po).map(n => n.name).join(', '));
    console.log('Aktywny:', po.active);
    process.exit(0);
  }

  console.error('Tryby: sprawdz | zapisz | cofnij <plik-kopii>');
  process.exit(1);
})();
