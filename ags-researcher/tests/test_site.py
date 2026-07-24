"""Testy lokalne zrodla 'site' (kaskada Researchera czyta strone badanego podmiotu).
Stdlib only, ZERO sieci: httpx podstawiony stubem, ktory oddaje przygotowany HTML.
Uruchomienie: python ags-researcher/tests/test_site.py"""
import pathlib
import sys
import types

BASE = pathlib.Path(__file__).resolve().parents[1] / "app"

# --- stub httpx (przed importem app.site) ---
fake_httpx = types.ModuleType("httpx")


class _Resp:
    def __init__(self, url, text, status=200):
        self.url = url
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _Client:
    STRONY = {}          # adres -> html; brak adresu = wyjatek (jak DNS bez wpisu)
    ODWIEDZONE = []

    def __init__(self, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url):
        _Client.ODWIEDZONE.append(url)
        if url not in _Client.STRONY:
            raise RuntimeError(f"No address associated with hostname ({url})")
        return _Resp(url, _Client.STRONY[url])


fake_httpx.Client = _Client
sys.modules["httpx"] = fake_httpx

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

fake_config = types.ModuleType("app.config")
fake_config.SOURCE_POLICY = {"low": ["site", "web_search"], "medium": ["site", "web_search"]}
fake_config.DEPLOYED_ADAPTERS = {"site", "web_search"}
fake_config.NATIVE_SOURCES = {"site"}
fake_config.active_sources = lambda level: [s for s in fake_config.SOURCE_POLICY.get(level, [])
                                            if s in fake_config.DEPLOYED_ADAPTERS]
sys.modules["app.config"] = fake_config

from app import router, site  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ---------------- adres z zapytania ----------------
print("\n[site] wyluskanie adresu z zapytania:")
Q_SPRZEDAZ = ("Prospect research dla sprzedazy B2B (AGS): Klub Sportowy StandART, "
              "strona: klubsportowystandart.org. Ustal: 1) czym jest ta firma...")
check("'strona: <domena>' z szablonu Sprzedawcy",
      site.extract_url(Q_SPRZEDAZ) == "klubsportowystandart.org", site.extract_url(Q_SPRZEDAZ))
check("goly link https", site.extract_url("Zbadaj https://przyklad.pl/oferta prosze")
      == "https://przyklad.pl/oferta")
check("kropka na koncu zdania nie wchodzi do adresu",
      site.extract_url("Zbadaj https://przyklad.pl.") == "https://przyklad.pl")
check("arxiv odrzucony (to nie strona podmiotu)",
      site.extract_url("porownaj z https://arxiv.org/abs/1234.5678") is None)
check("linkedin odrzucony", site.extract_url("profil https://linkedin.com/in/ktos") is None)
check("pytanie tematyczne bez adresu = None",
      site.extract_url("Jakie sa trendy w automatyzacji sprzedazy w 2026?") is None)

print("\n[site] router odsiewa 'site' bez adresu:")
r = router.QueryRouter()
check("zapytanie z adresem -> site w kaskadzie", "site" in r.sources("medium", Q_SPRZEDAZ),
      r.sources("medium", Q_SPRZEDAZ))
check("zapytanie tematyczne -> bez site", "site" not in r.sources("medium", "trendy w AI 2026"),
      r.sources("medium", "trendy w AI 2026"))
check("web_search zostaje zawsze", "web_search" in r.sources("medium", "trendy w AI 2026"))

# ---------------- warianty adresu ----------------
print("\n[site] warianty adresu (dowod 24/07: gola domena bez wpisu DNS):")
war = site.kandydaci_url("klubsportowystandart.org")
check("pierwszy wariant to www + https", war[0] == "https://www.klubsportowystandart.org", war)
check("cztery warianty (www/bez, https/http)", len(war) == 4, war)
check("pelny adres zostaje bez zmian",
      site.kandydaci_url("https://przyklad.pl/") == ["https://przyklad.pl"])

# ---------------- pobranie strony ----------------
HTML_GLOWNA = """<html><head><style>.x{color:red}</style></head><body>
<h1>Klub Sportowy StandART</h1>
<p>Zajecia taneczne dla dzieci i doroslych w Opolu. Zapraszamy!</p>
<a href="/kontakt">Kontakt</a> <a href="/blog/nowosci">Blog</a>
<script>var a=1;</script>
<footer>tel. 510 555 099, mail: recepcja@klubsportowystandart.org, NIP: 754 123 45 67</footer>
</body></html>"""
HTML_KONTAKT = "<html><body><h2>Kontakt</h2><p>Recepcja czynna 9-20. Adres: Opole, ul. Taneczna 1.</p></body></html>"

_Client.STRONY = {
    "https://www.klubsportowystandart.org": HTML_GLOWNA,
    "https://www.klubsportowystandart.org/kontakt": HTML_KONTAKT,
}
_Client.ODWIEDZONE = []

print("\n[site] pobranie i dowody:")
wynik = site.run({"url": "klubsportowystandart.org"})
check("status completed", wynik["status"] == "completed", wynik.get("error"))
check("koszt zerowy (zrodlo natywne)", wynik.get("cost_usd") == 0, wynik.get("cost_usd"))
pierwszy = wynik["evidence"][0]["content"]
check("PIERWSZY dowod to wyciag kontaktowy", pierwszy.startswith("DANE ZE STRONY PODMIOTU"), pierwszy[:60])
check("telefon zdjety ze stopki", "510 555 099" in pierwszy, pierwszy)
check("mail zdjety ze stopki", "recepcja@klubsportowystandart.org" in pierwszy, pierwszy)
check("NIP zdjety", "754 123 45 67" in pierwszy, pierwszy)
check("wyciag miesci sie w limicie syntezy (1200 znakow)", len(pierwszy) < 1200, len(pierwszy))
check("weszlismy na podstrone kontakt",
      any(e["source_url"].endswith("/kontakt") for e in wynik["evidence"]),
      [e["source_url"] for e in wynik["evidence"]])
check("blog NIE zostal pobrany (nie ma go na liscie podstron)",
      not any("blog" in u for u in _Client.ODWIEDZONE), _Client.ODWIEDZONE)
tresc = " ".join(e["content"] for e in wynik["evidence"])
check("tresc strony w dowodach", "Zajecia taneczne dla dzieci" in tresc)
check("skrypty i style wyciete", "var a=1" not in tresc and "color:red" not in tresc)
check("kazdy dowod ma authority 1.0", all(e["authority"] == 1.0 for e in wynik["evidence"]))
check("kazdy dowod ma source_name site", all(e["source_name"] == "site" for e in wynik["evidence"]))
check("liczba dowodow w rozsadku", len(wynik["evidence"]) <= 10, len(wynik["evidence"]))

print("\n[site] przypadki brzegowe:")
check("brak adresu w payloadzie = skipped", site.run({})["status"] == "skipped")
_Client.STRONY = {}
pusty = site.run({"url": "nieistniejaca-domena-xyz.pl"})
check("zadna wersja adresu nie odpowiada = empty", pusty["status"] == "empty", pusty)
check("empty niesie powod w error", "nie odpowiedziala" in (pusty.get("error") or ""), pusty)

_Client.STRONY = {"https://www.pusta.pl": "<html><body></body></html>"}
chuda = site.run({"url": "pusta.pl"})
check("strona bez tresci = empty, nie falszywy sukces", chuda["status"] == "empty", chuda)

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
