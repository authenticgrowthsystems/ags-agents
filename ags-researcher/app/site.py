"""Zrodlo 'site': pobranie STRONY BADANEGO PODMIOTU, natywnie w Pythonie (bez n8n, bez API,
bez kosztu).

DLACZEGO ISTNIEJE (dowod z jobu 7411d0ba, 24/07/2026): research prospekta orzekl "brak danych
kontaktowych", a telefon stoi na stronie glownej klubu. Sonda pokazala wade POBIERANIA, nie
syntezy: `web_search` zwrocil z domeny podmiotu SAME TYTULY (22-52 znaki), a adapter
`firecrawl` wola endpoint `/v2/search/research/papers` - czyli wyszukiwarke prac naukowych,
nie crawler zadanego adresu (stad osiem linkow z arXiv o "prospectingu AI").

Agent Sprzedazy obszedl to sam (`sales.wizytowka`), ale obejscie dotyczylo TYLKO sprzedazy -
kazdy inny konsument Researchera dostawal dalej tytuly zamiast tresci. To jest ta sama zdolnosc
przeniesiona do kaskady, wiec korzysta z niej kazdy zleceniodawca.

Zasada: pierwszym zrodlem prawdy o podmiocie jest jego wlasna strona. Zero LLM, zero sekretow,
kazdy blad konczy sie pustym wynikiem, nigdy wyjatkiem w gore.
"""
import datetime
import re

import httpx

TIMEOUT_S = 15
MAX_PAGES = 3            # strona glowna + do 3 podstron
PAGE_CHARS = 1100        # synteza tnie kazdy dowod na 1200 znakow - kawalek musi sie zmiescic
MAX_CHUNKS_PER_PAGE = 2
MAX_EVIDENCE = 10

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AGS-Researcher/1.0)"}
_TAGI_RE = re.compile(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>|<[^>]+>")
# podstrony, ktore u malych firm niosa kontakt i oferte (te same, co w sales.wizytowka)
_PODSTRONY_RE = re.compile(r"kontakt|contact|cennik|price|zapisy|grafik|instruktor|team|o-nas|about",
                           re.IGNORECASE)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# telefon PL: opcjonalny +48, potem 9 cyfr w typowym grupowaniu (NIP-y i daty odpadaja)
_PHONE_RE = re.compile(r"(?<![\d-])(?:\+48[\s-]?)?(?:\d{3}[\s-]?\d{3}[\s-]?\d{3})(?![\d-])")
_NIP_RE = re.compile(r"NIP[:\s]*([0-9][0-9\s-]{8,14})", re.IGNORECASE)

# adres podmiotu w zapytaniu: 'strona: <url>' (szablon Sprzedawcy), 'url:', 'site:' albo goly link
_URL_PO_ETYKIECIE = re.compile(r"(?:strona|url|site|www\s*:)\s*:?\s*(https?://\S+|www\.[^\s,;]+|"
                               r"[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(?:/\S*)?)", re.IGNORECASE)
_URL_GOLY = re.compile(r"https?://[^\s\)\]\|,>\"']+", re.IGNORECASE)
# adresy, ktore NIE sa strona podmiotu (agregatory, nauka, przekierowania wyszukiwarek)
_URL_SMIECI = re.compile(r"vertexaisearch|googleusercontent|google\.com/url|arxiv\.org|wikipedia|"
                         r"youtube\.com|facebook\.com|instagram\.com|linkedin\.com|tiktok\.com|"
                         r"aleo\.com|panoramafirm|targeo|rejestr\.io|krs-online", re.IGNORECASE)


def extract_url(query):
    """Adres podmiotu z tekstu zapytania albo None. Najpierw etykieta ('strona: ...'), potem
    pierwszy sensowny goly link. Adresy agregatorow i nauki odrzucamy - nie o nich pytamy."""
    q = query or ""
    m = _URL_PO_ETYKIECIE.search(q)
    if m:
        kandydat = m.group(1).rstrip(".,;)")
        if not _URL_SMIECI.search(kandydat):
            return kandydat
    for m in _URL_GOLY.finditer(q):
        kandydat = m.group(0).rstrip(".,;)")
        if not _URL_SMIECI.search(kandydat):
            return kandydat
    return None


_PODMIOT_FRAZY = ("prospect research", "research prospekta", "badanie podmiotu", "o firmie",
                  "wizytowka", "kim jest firma")


def zapytanie_o_podmiot(query):
    """Czy to pytanie o KONKRETNY PODMIOT (firma, osoba), a nie o temat.

    Sluzy dwom rzeczom: uruchomieniu zrodla 'site' i ZABLOKOWANIU cache semantycznego.
    Cache semantyczny liczy podobienstwo TEKSTU, a prompty prospektowe roznia sie tylko
    nazwa firmy - podobienstwo przekracza prog i "trafienie" oddaje dane INNEJ firmy
    (24/07: 6 jobow z cudza firma). Wykrywanie po samej frazie 'prospect research' bylo
    plastrem: kazdy nowy szablon zapytania go omijal (AP-307). Adres w zapytaniu jest
    mocniejszym i ogolniejszym sygnalem - niesie go kazde pytanie o konkretny podmiot."""
    q = (query or "").lower()[:200]
    return bool(extract_url(query)) or any(f in q for f in _PODMIOT_FRAZY)


def kandydaci_url(adres):
    """Warianty adresu do sprobowania. Dowod potrzeby (24/07): w lejku stoi
    'klubsportowystandart.org', a ta GOLA domena nie ma wpisu DNS - odpowiada wylacznie
    'www.klubsportowystandart.org'. Male strony bywaja tez bez certyfikatu, stad http."""
    a = (adres or "").strip().rstrip("/")
    if a.lower().startswith("http"):
        return [a]
    host = a.lstrip("/")
    bez_www = host[4:] if host.lower().startswith("www.") else host
    return [f"https://www.{bez_www}", f"https://{bez_www}",
            f"http://www.{bez_www}", f"http://{bez_www}"]


def _tekst(html):
    return re.sub(r"\s+", " ", _TAGI_RE.sub(" ", html or "")).strip()


def _podstrony(html, baza, limit):
    """Linki do podstron niosacych kontakt i oferte, w kolejnosci wystepowania."""
    out, widziane = [], {baza.rstrip("/")}
    for m in re.finditer(r'href=["\']([^"\'#]+)["\']', html or "", re.IGNORECASE):
        href = m.group(1)
        if not _PODSTRONY_RE.search(href):
            continue
        pelny = href if href.lower().startswith("http") else baza.rstrip("/") + "/" + href.lstrip("/")
        if pelny.rstrip("/") in widziane:
            continue
        widziane.add(pelny.rstrip("/"))
        out.append(pelny)
        if len(out) >= limit:
            break
    return out


def pobierz(url, max_pages=MAX_PAGES):
    """[(adres, tekst)] dla strony glownej i podstron. Pusta lista = nic nie odpowiedzialo."""
    strony = []
    try:
        with httpx.Client(timeout=TIMEOUT_S, follow_redirects=True, headers=_HEADERS) as klient:
            glowna, html = None, ""
            for kandydat in kandydaci_url(url):
                try:
                    rr = klient.get(kandydat)
                    rr.raise_for_status()
                    glowna, html = str(rr.url), rr.text
                    break
                except Exception:
                    continue
            if not glowna:
                return []
            strony.append((glowna, _tekst(html)))
            for link in _podstrony(html, glowna, max_pages):
                try:
                    rr = klient.get(link)
                    if rr.status_code == 200:
                        strony.append((link, _tekst(rr.text)))
                except Exception:
                    continue
    except Exception:
        return strony
    return strony


def _fakty_kontaktowe(tekst):
    """Krotki wyciag, ktory ZAWSZE zmiesci sie w limicie syntezy (1200 znakow na dowod).
    Bez tego numer telefonu z naglowka strony ginal przy ciecu dlugiego tekstu."""
    bity = []
    m = _EMAIL_RE.search(tekst or "")
    if m:
        bity.append(f"mail: {m.group(0)}")
    t = _PHONE_RE.search(tekst or "")
    if t:
        bity.append(f"telefon: {t.group(0).strip()}")
    n = _NIP_RE.search(tekst or "")
    if n:
        # uwaga: odwrotny ukosnik NIE moze wejsc do wyrazenia f-stringa (Python 3.11 w kontenerze)
        nip = re.sub(r"\s+", " ", n.group(1)).strip()
        bity.append(f"NIP: {nip}")
    return bity


def run(payload):
    """Kontrakt zrodla (taki sam, jak u adapterow n8n): {status, evidence[], cost_usd}.
    'skipped' = zapytanie nie niesie adresu; 'empty' = adres nie odpowiedzial."""
    url = (payload or {}).get("url")
    if not url:
        return {"status": "skipped", "evidence": []}
    strony = pobierz(url, int((payload or {}).get("max_pages") or MAX_PAGES))
    if not strony:
        return {"status": "empty", "evidence": [], "cost_usd": 0,
                "error": f"strona nie odpowiedziala na zaden wariant adresu ({url})"}
    stempel = datetime.date.today().strftime("%Y-%m-%d")
    calosc = " ".join(t for _u, t in strony)
    ev = []
    fakty = _fakty_kontaktowe(calosc)
    if fakty:
        # dowod nr 1: krotki, twardy, zawsze widoczny dla syntezy
        ev.append({"source_url": strony[0][0], "source_name": "site", "freshness": stempel,
                   "authority": 1.0,
                   "content": "DANE ZE STRONY PODMIOTU (zdjete bezposrednio, "
                              f"{stempel}): " + "; ".join(fakty)})
    for adres, tekst in strony:
        if not tekst:
            continue
        for i in range(MAX_CHUNKS_PER_PAGE):
            kawalek = tekst[i * PAGE_CHARS:(i + 1) * PAGE_CHARS]
            if not kawalek.strip():
                break
            ev.append({"source_url": adres, "source_name": "site", "freshness": stempel,
                       "authority": 1.0,
                       "content": f"TRESC STRONY {adres} (czesc {i + 1}): {kawalek}"})
            if len(ev) >= MAX_EVIDENCE:
                break
        if len(ev) >= MAX_EVIDENCE:
            break
    if not ev:
        return {"status": "empty", "evidence": [], "cost_usd": 0,
                "error": f"strona odpowiedziala, ale nie zostalo z niej nic czytelnego ({url})"}
    return {"status": "completed", "evidence": ev, "cost_usd": 0}
