# BRIEF BUILDU: PRODUKT DFY - System Retencji Klientow (20072026) - budowniczy: BE-PRODUKT

Wywolanie (Fable 5 max 2 prompty -> Opus 4.8 konczy):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_PRODUKT_DFY_RETENCJA_20072026.md zbuduj`
CZYTAJ: brief Managera C:\Claude-CoWork\AGS\BE_BRIEF_AGENT_SPRZEDAZY_MVP_20072026.md (SEKCJA 3)
+ docs/GOTOWOSC_PRODUKTU.md. KRYZYS = produkt ma byc OFEROWALNY DZIS.

## 0. Tryb rownolegly
Worktree+galaz `build/produkt-dfy` od origin/claude/silly-blackwell-dfc32d. Build czysto
DOKUMENTOWO-OFERTOWY: zero kodu, zero DDL, zero n8n, zero deployu. Merge przez integratora.

## 1. CO budujemy (sprzedawalny pakiet DZIS)

**Produkt:** DFY "System Retencji Klientow" dla malych firm (PL start, hybryda PL/US).
Sedno wg Tomasza: male firmy nie potrzebuja skomplikowanej automatyzacji, tylko
USZCZELNIENIA, zeby klient im nie uciekal. Wewnetrznie GHL - NAZWY NARZEDZIA NIE UJAWNIAMY
(sprzedajemy rezultat). Model: setup one-time (praca Tomasza w DFY) + klient placi narzedzie
SAM (wlasny sub-account); przyszlosc: SaaS white label.

Deliverables (docs/product/):
1. **OFERTA_DFY_RETENCJA.md** - one-pager oferty w Voice Bible (PL + EN wersja; kanon
   walutowy: PL=PLN, EN=USD): problem (uciekajacy klienci) -> rezultat (powracajacy,
   follow-up ktory sie dzieje sam) -> co dostaje (lista DFY z sekcji 3 briefu Managera:
   setup, sekwencje follow-up email/SMS, brandowanie, 2-4 sesje treningu, runbook) ->
   cena wg pricing_tiers: uzyj ISTNIEJACYCH parking_active "Pakiet 1/2/3" (2000-3000 /
   3000-5000 / 5000-8000 PLN + abonament narzedzia $97-297/mc placony przez klienta) -
   zaproponuj aktywacje tych tierow (meta_status active) + mapowanie na EN (USD).
   ZAKAZ /apply w tresci (doktryna). CTA = odpowiedz na wiadomosc / krotka rozmowa.
2. **RUNBOOK_DFY_RETENCJA.md** - krok po kroku wdrozenie u klienta (dla Tomasza, po polsku,
   test krzeslem): discovery 30 min -> setup sub-account -> pipeline/etapy -> sekwencje
   follow-up (szablony tresci per branza: 3 przyklady - uslugi lokalne, studio/szkola,
   freelancer) -> branding -> testy -> szkolenie klienta -> przekazanie + maintenance.
   Zrodla: funnel_configs, sales_sequences, vendor_registry, sales_playbook (czytaj z DB
   read-only przez temp webhook - slowniczek w masterprompcie 2b) + wiedza generalna GHL.
3. **FAQ_OBJEKCJE.md** - top 10 objekcji malej firmy + odpowiedzi w Voice Bible (bez zargonu).
4. Aktualizacja GOTOWOSC_PRODUKTU.md: nowy obiekt sprzedazowy "DFY System Retencji" =
   SPRZEDAWALNY (praca reczna Tomasza + narzedzie; zaleznosc: tylko czas Tomasza).

DoD: Tomasz czyta oferte i moze ja wyslac prospektowi BEZ poprawek; runbook przechodzi test
krzeslem; SQL aktywacji tierow (meta_status) przygotowany do decyzji Tomasza guzikami.

## 5. Udzial Tomasza
Decyzja guzikami: aktywacja Pakietow 1-3 + ostateczne kwoty; test krzeslem runbooka.

## 6. Zamkniecie: raport + macierz + STATUS tu. STATUS = READY (20/07 ~13:20)
