# SALES MANAGER + DEDYKOWANI OPIEKUNOWIE KLIENTA - kanon architektury (22/07/2026)

Wymog Tomasza 22/07 (przed telefonem Adamietz): sprzedaz ma miec TE SAMA architekture
nadzoru co content. Content Manager odpowiada za subagentow kanalowych - analogicznie
**Sales Manager** odpowiada za **subagentow-opiekunow**, z ktorych kazdy jest DEDYKOWANY
JEDNEMU klientowi/prospektowi. Liczba opiekunow moze rownac sie liczbie klientow.

## Zasady kanonu

1. **1 opiekun = 1 klient.** Opiekun zna caly kontekst swojego klienta (research,
   relacje, historia rozmow, preferencje, wspolne tematy) i tylko jego. Sprzedajemy
   relacjami i emocjami - opiekun ma znac czlowieka, nie segment.
2. **Stan spoczynku.** Klient obsluzony / stracony -> opiekun przechodzi w spoczynek
   (nie kasujemy). Reaktywacja klienta = reaktywacja opiekuna z PELNA pamiecia.
3. **DZIENNIK KAPITANSKI (log log).** Cala praca opiekuna zapisywana chronologicznie,
   najprosciej jak sie da (append-only, czytelne dla czlowieka): co sie wydarzylo,
   po kolei, z datami. Cel: ratowanie kontaktu / ponowna obsluga po latach wymaga
   TYLKO przeczytania dziennika.
4. **Pelny research przed wspolpraca.** Zanim opiekun zacznie prace: kompletny
   research klienta (firma + CZLOWIEK: co lubi, co robi, wspolne tematy). Critical
   research recznie na abonamentach (kanon kosztowy 20/07), zrzut do kartoteki.

## Mapowanie na obecna architekture (co JUZ jest)

- Kartoteka klienta = sales_pipeline (etap, wartosc, next_followup) + contacts
  (tozsamosc, tier, stadium relacji) + engagement_log (kazda interakcja) +
  sales_knowledge (wiedza). To jest JUZ pamiec per klient - opiekun jej uzywa.
- Silnik jest WSPOLNY (jak subagenci kanalowi: jeden kod, konfiguracja z bazy).
  "Dedykowany opiekun" = OBIEKT (kartoteka + dziennik + kontekst wstrzykiwany do
  rozmowy), NIE osobny proces per klient. Stan spoczynku = pole statusu kartoteki.
- Agent Sprzedazy L1 (LIVE od 20/07) pelni dzis OBIE role naraz: managera i jedynego
  opiekuna. To swiadome MVP - patrz luki.

## Co trzeba DOBUDOWAC (do decyzji Managera - poziomy L2/L3)

1. **Dziennik kapitanski jawny**: append-only log per klient (najprostszy format
   tekstowy, eksportowalny), skladany automatycznie z engagement_log + notatek lejka
   + decyzji; komenda "pokaz dziennik <klient>".
2. **Rozdzial rol**: Sales Manager (strategia, priorytety lejka, przydzial opiekunow,
   raporty do Tomasza) vs opiekun (kontekst 1 klienta w kazdej rozmowie/outreachu).
   Technicznie: tryb rozmowy "jako opiekun <klienta>" z wstrzyknieta kartoteka.
3. **Cykl zycia opiekuna**: aktywny -> spoczynek (klient zamkniety) -> reaktywacja.
4. **Research-przed-wspolpraca jako bramka**: nowy klient bez kompletnej kartoteki
   researchowej = opiekun NIE zaczyna sprzedazy, tylko prosi o research.

## DECYZJE MANAGERA (22/07, odpowiedz na zapytanie) - CANONICAL

- **P1 kolejnosc:** DZIENNIK KAPITANSKI PIERWSZY (maly, natychmiast uzyteczny przy
  Adamietz) -> Stripe -> wysylka DFY Adamietz -> Gmail L2 -> rozdzial rol (po 3
  klientach). Reszta poziomow po first close.
- **P2 tryb:** Sprzedawca laczy role dopoki klientow < 5. Progi: 5 = przelacznik
  trybow Manager/opiekun w kodzie; 20 = osobny agent Sales Manager w /agents +
  opiekunowie jako sub-agenty.
- **P3:** ten plik = source of truth architektury sprzedazowej (poziomy L1-L4).
  Do Voice Bible dojdzie sekcja "Sales voice per opiekun" (glos RELACYJNY per klient,
  NIE jeden wspolny cross-portfolio) - bump VB przy najblizszej iteracji (backlog).

STATUS: DZIENNIK KAPITANSKI ZBUDOWANY 22/07 (sales.py: /dziennik <klient> +
narzedzie dziennik_klienta; widok na append-only zrodla, dlugi dziennik = plik .md;
przepustka n8n nalozona). Wchodzi na serwer z najblizszym rebuildem (integracja
Lacznika). Nastepne wg P1: Stripe (decyzja D2 researchu) -> wysylka DFY.
