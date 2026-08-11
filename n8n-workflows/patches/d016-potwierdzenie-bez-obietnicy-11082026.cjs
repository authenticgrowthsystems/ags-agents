// D-016 (11/08/2026): potwierdzenie po tapnieciu guzika obiecuje publikacje "za chwile"
// niezaleznie od tego, kiedy naprawde wypadnie slot.
//
// OBJAW, ktory zglosil Tomasz 10/08 - dwie wiadomosci w tym samym czacie, ta sama minuta 18:09:
//     "✅ Zatwierdzono. Publikacja za chwile. Potwierdzenie przyjdzie na kanale logowym."
//     "🗓 CM przydzielil slot: Tue 11/08 16:00"
// "Za chwile" i "za dwadziescia dwie godziny" w jednym oddechu. To jest AP-312 w wydaniu
// czasowym: etykieta obiecuje co innego, niz sie stanie.
//
// DLACZEGO TO NIE JEST KOSMETYKA. Przy czterech publikacjach dziennie czlowiek dostaje te pare
// wiadomosci kilka razy dziennie. Zdanie, ktore systematycznie klamie, uczy ignorowac CALY kanal
// - a tym samym kanalem ida alarmy zwisu publikacji i meldunki bezpiecznika gatunku. Koszt nie
// jest w tej jednej wiadomosci, tylko w zaufaniu do reszty.
//
// ============================================================================
// UWAGA, TEN PATCH ROZNI SIE OD `d008-handed-off`: tam gaszony byl Scheduler (cron), tu gaszony
// jest HITL Handler, czyli JEDYNY interfejs Tomasza. Przez okno patcha guziki w bocie nie
// odpowiadaja. Dlatego `patch` SAM WRACA do gry na koncu, zamiast zostawiac wylaczony workflow.
// Okno liczy sie w sekundach - ale odpal to, gdy nie czekasz na zadna decyzje.
// ============================================================================
//
// CZEGO TEN SKRYPT NIE ZAKLADA. Eksport HITL Handlera w repo jest z 11/06 i NIE ZAWIERA wezla,
// ktory ten napis trzyma - definicja zywa rozjechala sie z repo o dwa miesiace. Dlatego skrypt
// NIE szuka wezla po nazwie. Przeszukuje CALA definicje rekurencyjnie, po tresci, i w trybie
// `sprawdz` drukuje sciezke do kazdego trafienia razem z pelnym otoczeniem. Najpierw patrzysz,
// potem podmieniasz.
//
// UZYCIE (Bash, z katalogu repozytorium):
//   set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' \
//       "C:/Claude-CoWork/AGS/ags-agents/.env" | sed 's/\r$//') && set +a
//   node n8n-workflows/patches/d016-potwierdzenie-bez-obietnicy-11082026.cjs sprawdz  # tylko odczyt
//   node n8n-workflows/patches/d016-potwierdzenie-bez-obietnicy-11082026.cjs patch    # PUT + powrot do gry
//   node n8n-workflows/patches/d016-potwierdzenie-bez-obietnicy-11082026.cjs cofnij   # ratunek
//
// PAMIETAJ (project_n8n_reactivate_after_put): PUT zapisuje definicje do bazy, ale AKTYWNY
// snapshot trzyma STARA. Bez deactivate+activate bot dalej odpowiada wersja sprzed PUT-a.

const fs = require('fs');

const ID = 'U5pUZjy2yAhR1sWg';
const NAZWA = 'AGS HITL Handler v1.0';

// Szukamy po FRAGMENCIE, nie po calym zdaniu: nie wiem, czy zywa definicja ma polskie znaki
// (bot dostal pelna polszczyzne 2c62b3f, ale ten napis moze byc starszy). Oba warianty naraz.
const WARIANTY = ['Publikacja za chwilę.', 'Publikacja za chwile.'];

// Zdanie zastepcze jest PRAWDZIWE W KAZDYM PRZYPADKU - i to jest cala robota tego patcha.
// NIE obiecuje meldunku o godzinie: CM melduje slot tylko wtedy, gdy go WLASNIE przydzielil
// (`slots.assign_if_needed` zwraca changed=False, gdy material slot juz mial). Obietnica
// meldunku byla by tym samym bledem, tylko przesunietym o jedno zdanie.
const NOWE = 'Materiał czeka na swój slot - publikacja nie idzie od razu.';

const ALLOWED = ['saveDataErrorExecution', 'saveDataSuccessExecution', 'saveManualExecutions',
  'saveExecutionProgress', 'executionTimeout', 'errorWorkflow', 'timezone', 'executionOrder'];

const base = process.env.N8N_BASE_URL;
const key = process.env.N8N_API_KEY;
if (!base || !key) { console.error('BRAK N8N_BASE_URL / N8N_API_KEY w srodowisku.'); process.exit(1); }
const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };

const spij = (ms) => new Promise(r => setTimeout(r, ms));

async function pobierz() {
  const r = await fetch(`${base}/api/v1/workflows/${ID}`, { headers: H });
  if (!r.ok) { console.error('GET nieudany:', r.status, await r.text()); process.exit(1); }
  return r.json();
}

// Rekurencyjny przejazd po parametrach wezla: napis moze siedziec w `text`, w `jsCode`,
// w galezi `additionalFields`, gdziekolwiek. Zwraca liste {sciezka, wartosc}.
function znajdz(obj, igly, sciezka = '') {
  let out = [];
  if (typeof obj === 'string') {
    if (igly.some(i => obj.includes(i))) out.push({ sciezka, wartosc: obj });
    return out;
  }
  if (Array.isArray(obj)) {
    obj.forEach((v, i) => { out = out.concat(znajdz(v, igly, `${sciezka}[${i}]`)); });
    return out;
  }
  if (obj && typeof obj === 'object') {
    for (const k of Object.keys(obj)) out = out.concat(znajdz(obj[k], igly, sciezka ? `${sciezka}.${k}` : k));
  }
  return out;
}

function podmien(obj, z, na) {
  let ile = 0;
  const chodz = (o) => {
    if (Array.isArray(o)) { o.forEach((v, i) => { if (typeof v === 'string' && v.includes(z)) { o[i] = v.split(z).join(na); ile++; } else chodz(v); }); return; }
    if (o && typeof o === 'object') {
      for (const k of Object.keys(o)) {
        const v = o[k];
        if (typeof v === 'string' && v.includes(z)) { o[k] = v.split(z).join(na); ile++; }
        else chodz(v);
      }
    }
  };
  chodz(obj);
  return ile;
}

function raport(w, igly) {
  const trafienia = [];
  for (const n of w.nodes) {
    for (const t of znajdz(n.parameters || {}, igly, '')) {
      trafienia.push({ wezel: n.name, typ: n.type, ...t });
    }
  }
  return trafienia;
}

async function sprawdz(cisza) {
  const w = await pobierz();
  const stare = raport(w, WARIANTY);
  const nowe = raport(w, [NOWE]);
  if (!cisza) {
    console.log(`${NAZWA} | aktywny: ${w.active} | wezlow: ${w.nodes.length}`);
    console.log(`\nTRAFIENIA na stary napis: ${stare.length}`);
    for (const t of stare) {
      console.log(`\n  wezel : ${t.wezel}  (${t.typ})`);
      console.log(`  pole  : parameters.${t.sciezka}`);
      console.log(`  tresc : ${JSON.stringify(t.wartosc).slice(0, 400)}`);
    }
    console.log(`\nTRAFIENIA na nowy napis (po patchu ma byc tyle, ile bylo starych): ${nowe.length}`);
    if (!stare.length && !nowe.length) {
      console.log('\nUWAGA: nie znalazlem ANI starego, ANI nowego napisu.');
      console.log('Zywa definicja moze uzywac innego sformulowania niz zrzut z 10/08.');
      console.log('NIE zgaduj - przejrzyj wezly recznie w n8n i popraw stale WARIANTY w tym pliku.');
    }
  }
  return { w, stare, nowe };
}

async function patch(kierunek) {
  const cofamy = kierunek === 'cofnij';
  const { w, stare, nowe } = await sprawdz(true);
  const zrodlo = cofamy ? nowe : stare;

  if (zrodlo.length === 0) {
    console.error(`STOP: zero trafien na napis, ktory mam podmienic. Nic nie wysylam.`);
    console.error('Odpal najpierw: node ... sprawdz  - i przeczytaj, co tam naprawde stoi.');
    process.exit(1);
  }
  if (zrodlo.length > 3) {
    console.error(`STOP: ${zrodlo.length} trafien to wiecej, niz ten patch zaklada (max 3).`);
    console.error('Definicja jest inna, niz mysle. NIE zgaduj - przeczytaj ja recznie.');
    process.exit(1);
  }
  console.log(`Do podmiany: ${zrodlo.length} miejsc`);
  for (const t of zrodlo) console.log(`  ${t.wezel} -> parameters.${t.sciezka}`);

  const kopia = `${__dirname}/bk_hitl_d016_${Date.now()}.json`;
  fs.writeFileSync(kopia, JSON.stringify(w, null, 2));
  console.log('kopia zapasowa:', kopia);

  let zmienionych = 0;
  for (const n of w.nodes) {
    if (cofamy) {
      zmienionych += podmien(n.parameters || {}, NOWE, WARIANTY[0]);
    } else {
      for (const wariant of WARIANTY) zmienionych += podmien(n.parameters || {}, wariant, NOWE);
    }
  }
  if (zmienionych !== zrodlo.length) {
    console.error(`STOP: podmienilem ${zmienionych} miejsc zamiast ${zrodlo.length}. Nic nie wysylam.`);
    process.exit(1);
  }

  // Gaszenie DOPIERO teraz: definicja jest juz przygotowana w pamieci, wiec okno bez guzikow
  // trwa tyle, co PUT i activate, a nie tyle, co caly przebieg skryptu.
  const de = await fetch(`${base}/api/v1/workflows/${ID}/deactivate`, { method: 'POST', headers: H });
  console.log('deactivate:', de.status);

  const settings = {};
  for (const k of ALLOWED) if (w.settings && w.settings[k] !== undefined) settings[k] = w.settings[k];
  const put = await fetch(`${base}/api/v1/workflows/${ID}`, { method: 'PUT', headers: H,
    body: JSON.stringify({ name: w.name, nodes: w.nodes, connections: w.connections, settings }) });
  console.log('PUT:', put.status);
  if (put.status !== 200) {
    console.error(await put.text());
    console.error('PRZYWRACAM AKTYWNOSC, zeby nie zostawic bota bez guzikow.');
    await fetch(`${base}/api/v1/workflows/${ID}/activate`, { method: 'POST', headers: H });
    process.exit(1);
  }

  // ODCZYT PO ZAPISIE: 200 znaczy "przyjalem", nie "zapisalem to, co myslisz".
  const po = await pobierz();
  const poStare = raport(po, WARIANTY).length;
  const poNowe = raport(po, [NOWE]).length;
  console.log(`po zapisie: stary napis ${poStare}, nowy napis ${poNowe}`);

  const ak = await fetch(`${base}/api/v1/workflows/${ID}/activate`, { method: 'POST', headers: H });
  console.log('activate:', ak.status);
  const kon = await pobierz();
  console.log(kon.active ? 'OK: workflow z powrotem aktywny.' : 'ZLE: workflow NIEAKTYWNY - wlacz recznie w n8n!');

  const dobrze = cofamy ? (poNowe === 0 && poStare === zrodlo.length)
                        : (poStare === 0 && poNowe === zrodlo.length);
  console.log(dobrze ? 'OK: definicja zapisana poprawnie.' : 'ZLE: definicja po zapisie sie nie zgadza.');
  console.log('\nPOTWIERDZENIE ZACHOWANIEM (project_n8n_reactivate_after_put): odpowiedz 200 i flaga');
  console.log('"active" NIE dowodza, ze bot chodzi na nowej definicji. Tapnij dowolny guzik w bocie');
  console.log('i zobacz, czy potwierdzenie brzmi po nowemu. Dopiero to jest dowod.');
  process.exit(dobrze && kon.active ? 0 : 1);
}

const tryb = process.argv[2];
if (tryb === 'sprawdz') sprawdz(false);
else if (tryb === 'patch' || tryb === 'cofnij') patch(tryb);
else {
  console.log('Tryby: sprawdz | patch | cofnij');
  console.log('Zawsze zaczynaj od `sprawdz` - eksport w repo jest z 11/06 i nie opisuje zywej definicji.');
  process.exit(1);
}
