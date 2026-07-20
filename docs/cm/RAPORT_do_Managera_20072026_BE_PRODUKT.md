# RAPORT do Managera: BE-PRODUKT (DFY System Retencji) - DONE (20/07/2026)

**Od:** BE-PRODUKT (Instance C briefu Managera 20/07, sekcja 3)
**Galaz:** build/produkt-dfy (od claude/silly-blackwell-dfc32d f2ac056; merge przez integratora)
**Charakter:** czysto dokumentowo-ofertowy. Zero kodu, zero DDL wykonanego, zero n8n, zero deployu.

## 1. Deliverables (komplet wg briefu)

| Plik | Co to jest |
|---|---|
| docs/product/OFERTA_DFY_RETENCJA.md | One-pager PL + EN, gotowy do wyslania 1:1. Sekwencja problem -> rezultat -> mechanizm -> cena (D2). Pakiety od premium w dol (top-down). Kwoty PL = 1:1 z pricing_tiers lokalna_automatyzacja. EN = propozycja USD powyzej prostego przeliczenia (D9). Zero nazwy GHL, zero /apply, CTA = odpowiedz na wiadomosc + 20 min rozmowy. Sekcje klienckie z pelnymi polskimi znakami. |
| docs/product/RUNBOOK_DFY_RETENCJA.md | Wdrozenie krok po kroku (0-10): discovery 30 min (lista pytan) -> konto klienta (WLASNE, $97/$297) -> fundament (DNS/e-mail z lekcjami z vendor_registry: 6 rekordow, MX FQDN z kropka) -> pipeline 7 etapow -> sekwencje z GOTOWYMI tresciami PL per branza (uslugi lokalne / studio-szkola z know-how RDC / freelancer B2B z kadencja ABM 48h/5d/8d) -> branding -> RODO -> testy (checklist "test krzeslem systemu") -> szkolenie 2-4 sesje (agendy) -> przekazanie + 30 dni gwarancji. Zalacznik: szablon wiadomosci do klienta po decyzji. |
| docs/product/FAQ_OBJEKCJE.md | 10 objekcji + odpowiedzi (Voss label -> odwrocenie, D18 zero rabatow, mom test, regula prawdy - zadnych zmyslonych wynikow). |
| docs/product/SQL_AKTYWACJA_PAKIETOW_PL_20072026.sql | Gotowiec: parking_active -> active (3 Pakiety PL) + opcjonalny INSERT drabinki retention_en (USD). WYKONUJE TOMASZ PO decyzji guzikami. |
| docs/GOTOWOSC_PRODUKTU.md | Nowy wiersz #1: DFY System Retencji = SPRZEDAWALNY (zaleznosc: tylko czas Tomasza); doprecyzowane dwa modele DFY (nasza infra vs wlasne konto klienta). |

## 2. Decyzje projektowe (do wiadomosci / ew. korekty Managera)

1. **Nazwy pakietow w ofercie** retencyjne (Kompletny System Retencji / Strona + Podstawowa
   Automatyzacja / Fundament), mapowanie na istniejace tier_name w notatce wewnetrznej oferty.
   Wiersze pricing_tiers NIE zmieniane (kwoty i zakres 1:1 z bazy).
2. **EN pricing = $700-1000 / $1200-1900 / $2500-3500** (nie proste przeliczenie ~$500-2000):
   rynek US, D9 cena=komunikat wartosci. Nowa drabinka retention_en, nie dotykam ags_premium.
3. **Abonament narzedzia w PL ofercie podany w USD z przelicznikiem** (~400-1200 zl): fakt
   w walucie zrodla (kanon walutowy pkt 15), klient placi vendorowi w USD - ukrywanie tego
   byloby pozorna prostota i niespodzianka na karcie.
4. **Zrodla DB (funnel_configs/sales_sequences/vendor_registry/sales_playbook) wziete z repo**
   (etl/notion/phase*.sql + raport 71-D = te same tresci co wiersze w bazie), bez stawiania
   temp webhooka: build bez dotykania n8n, a zawartosc identyczna. Kadencja ABM 48h/5d/8d
   i lekcje GHL/DNS skonsumowane w runbooku.
5. **RODO jako osobny krok runbooka** (import bazy, zgody, STOP) - PL malych firm o to pyta,
   objekcja #10 ma pokrycie w procedurze.

## 3. Dziury zalatane / zostajace (vs TOP5 z RAPORT_STAN_BUILDU)

- #2 oferta-dokument: DONE (ten build).
- #1 platnosc: NIE w zakresie briefu; oferta i runbook zakladaja FV + przelew (50% zaliczki)
  do czasu rekomendacji z BE-RESEARCH (build D). Nic w ofercie nie obiecuje platnosci online.
- #4 umowa/powierzenie RODO: wskazane w runbooku jako brakujacy wzorzec (do osobnego taska).
- Link partnerski GHL (40%): oznaczony w ofercie i runbooku jako "przygotowac przed pierwsza
  sprzedaza"; wdrozenie NIE jest od niego zalezne.

## 4. Czeka na Tomasza (guziki + test krzeslem)

1. Aktywacja Pakietow PL 1-3 (SQL gotowy) - rekomendacja: TAK, bez zmian kwot.
2. Kwoty EN retention_en - rekomendacja: przyjac propozycje z oferty.
3. Test krzeslem runbooka + przeczytanie oferty PL (DoD: wysylalna bez poprawek).

## 5. Dla integratora

Merge build/produkt-dfy do sb-work: tylko docs/ (5 plikow, w tym 1 modyfikacja
GOTOWOSC_PRODUKTU.md - przy konflikcie z innym buildem brac obie zmiany). SQL aktywacji
NIE wchodzi do paczki psql deployu (wykonanie = dopiero po decyzji Tomasza).
