# MACIERZ GOTOWOSCI PRODUKTU (stan: 20/07/2026 ~15:00, +DFY Retencja z buildu BE-PRODUKT)

Kanon: DOKUMENTACJA ZYJE pkt 6 - kazdy build aktualizuje ten plik w tym samym commicie.
Skala: KOMPLETNY (LIVE + tapy + dokumentacja) / CZESCIOWY (rdzen dziala, braki wymienione)
/ W BUDOWIE / ZAMROZONY / NIEZACZETY. Zero marketingu do wewnatrz.

## 1. JUTRO MAM KLIENTA - CO MOGE SPRZEDAC (model: done-for-you na NASZEJ infrastrukturze)

Do czasu playbooka wdrozeniowego (BE-SNAPSHOT, HOLD) sprzedajemy WYLACZNIE done-for-you.
Dwa rownolegle modele DFY: (a) agenci tresci = marka klienta jako nowy brand w NASZYM
systemie (/brand_add, multi-brand LIVE), Tomasz operuje; (b) DFY System Retencji = wdrozenie
na WLASNYM koncie narzedzia klienta (GHL, nazwa nieujawniana w sprzedazy) - niezalezne od
naszej infrastruktury agentowej, blokuje tylko czas Tomasza.
Model MVP rozwijany: rdzen dziala od dnia 1, funkcje doplywaja w cenie.

| Obiekt sprzedazowy | Status | Co klient dostaje DZIS | Co dojedzie w cenie |
|---|---|---|---|
| **DFY System Retencji Klientow** (praca reczna Tomasza + narzedzie GHL; NIE czesc naszej infrastruktury agentowej) | **SPRZEDAWALNY** (zaleznosc: TYLKO czas Tomasza) | wdrozenie od A do Z na WLASNYM koncie klienta: sciezka klienta (pipeline), sekwencje przypomnien e-mail/SMS, prosba o opinie Google, odzysk nieaktywnych, branding, 2-4 sesje szkolenia, instrukcja, 30 dni gwarancji; Pakiety PL 1-3 (2000-3000 / 3000-5000 / 5000-8000 PLN + narzedzie $97-297/mc placi klient); komplet: docs/product/OFERTA_DFY_RETENCJA.md + RUNBOOK + FAQ_OBJEKCJE | link partnerski narzedzia (40% cyklicznie), wzorzec umowy/powierzenia RODO (dziura #4 TOP5), opieka abonamentowa po 30 dniach, docelowo SaaS white label |
| **Subagent X pod nadzorem** | SPRZEDAWALNY (MVP) | plan tygodnia pod jego ICP (bramka tematow), tresci do akceptu 1 tapem, publikacja sama w ludzkich minutach, serie zamiast klocow, metryki per post (Owned Reads), raporty dzienne/tygodniowe, komentarze pod widocznosc (ze zrzutow) | CRM relacji przy komentowaniu (kto, stadium relacji, intake nowych osob, przypomnienia - build 20/07 czeka na wdrozenie), samodzielne polowanie na posty do komentowania (po baseline), X Articles |
| **Idea Bot** (lapacz pomyslow) | SPRZEDAWALNY (MVP) | pomysl tekstem/glosem/zdjeciem/wideo -> research -> seria postow PL+EN z decyzjami per post | glebsza integracja z planem tygodnia |
| **Researcher** (dodatek premium) | SPRZEDAWALNY z nota | badania 5 zrodel (web/firecrawl/gemini/openai DR/manus), cost-cascade, koszt per job widoczny | nota: naprawa web_search 20/07 - finalny dowod = sobotni cykl 26/07 |
| **Subagent LinkedIn** | CZESCIOWY | tresci + gotowce do RECZNEJ publikacji (gotowiec 1-tap copy), import metryk z eksportu xlsx | auto-publikacja i metryki API po review App 2 CMA (poza nasza kontrola czasowo) |
| **CM (caly orkiestrator)** | CZESCIOWY - NIE nazywac gotowym | planowanie tygodnia, rozmowa-partner, nadzor subagentow, eskalacje guzikami z nauka | kanon project_cm_real_scope: pelny CM = takze planowanie 2-mies., pelna autonomia nadzoru - W BUDOWIE |

## 2. CZEGO NIE SPRZEDAJEMY (wprost)

- **Agent Wizualny** - ZAMROZONY (spec gotowy; grafika dziala jako organ CM, nie produkt).
- **Wdrozenie self-hosted u klienta** - brak playbooka (BE-SNAPSHOT HOLD do gotowosci).
- **Pelna autonomia tresci** - kanon 19/07 wyklucza na zawsze (zatwierdza czlowiek).
- **Slack / web / mobile jako interfejs** - NIEZACZETE (dzis tylko Telegram; architektura
  gotowa na wymienne konektory, front webowy = przyszly build).

## 3. KOMPONENTY (szczegoly: docs/komponenty/*.md - status w naglowku kazdego pliku)

| Komponent | Status | Glowny brak |
|---|---|---|
| planner | KOMPLETNY | - |
| kolejka-publikacja | KOMPLETNY | - |
| karty-hitl | KOMPLETNY | - |
| decyzje-nauka | CZESCIOWY | mechanizm LIVE; nauka mloda (progi semi-auto nieosiagniete - potrzeba decyzji) |
| metryki | CZESCIOWY | X = auto (kolektor); LinkedIn = import xlsx reczny do App 2 CMA |
| dedup | KOMPLETNY | strojenie progu przez /set czeka na patch allowlisty (SQL dziala) |
| rozmowa-cm | CZESCIOWY | komendy configu routowane deterministycznie; poza nimi LLM moze "zameldowac bez narzedzia" (test prawdy: paragon) |
| researcher | KOMPLETNY z nota | dowod sobotniego cyklu 26/07 przed sprzedaza |
| grafika | CZESCIOWY | gpt-image-2 + kanon barw LIVE; brak assetow referencyjnych (zdjecia/loga) i wariantow per platforma (Agent Wizualny) |
| sync-notion | KOMPLETNY | - |
| n8n-transport | KOMPLETNY | - |
| engagement-crm | W BUDOWIE | kod + DDL 026 w build/engagement-crm; czeka merge + psql 026 + rebuild + patch n8n (media_group_id) + 5 tap-testow DoD |
| agent-sprzedazy | W BUDOWIE | kod + DDL 027 w build/sprzedawca (narzedzie wewnetrzne sprzedazy, nie produkt); czeka merge + psql 027 + rebuild (nowa zaleznosc pypdf) + patch n8n (komendy+pdf) + tap-testy DoD |

## 4. BRAKI BLOKUJACE SPRZEDAZ (per przekroj)

0. ~~SCIEZKA PLATNOSCI~~ ZALATANA 22/07: Tomasz MA dzialajace, zweryfikowane konto
   Stripe (NIP, wyplaty PLN; 3500+ PLN przyjete z rejestracji lekcji pierwszego tanca).
   Do sprzedazy DFY wystarczy Payment Link z uzgodniona kwota per deal (produkt-szablon
   "Wdrozenie systemu retencji klientow"; cena USD jako drugi price na tym samym
   produkcie). Otwarte pozostaje TYLKO wystawianie FV VAT (system ksiegowy Tomasza,
   nie Stripe) - dziura "umowa/FV" z TOP5.
1. Interfejs klienta = tylko Telegram (done-for-you to obchodzi: klient dostaje wyniki,
   opcjonalnie wlasny bot Telegram; self-service wymaga frontu webowego).
2. Wdrozenie = brak playbooka + intake 7 krokow (BE-SNAPSHOT HOLD).
3. Sprzedaz konkretnego agenta = sesja ofertowa z Managerem (gdy uruchomiony) z ta macierza.
