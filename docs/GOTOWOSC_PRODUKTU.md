# MACIERZ GOTOWOSCI PRODUKTU (stan: 20/07/2026 ~12:30)

Kanon: DOKUMENTACJA ZYJE pkt 6 - kazdy build aktualizuje ten plik w tym samym commicie.
Skala: KOMPLETNY (LIVE + tapy + dokumentacja) / CZESCIOWY (rdzen dziala, braki wymienione)
/ W BUDOWIE / ZAMROZONY / NIEZACZETY. Zero marketingu do wewnatrz.

## 1. JUTRO MAM KLIENTA - CO MOGE SPRZEDAC (model: done-for-you na NASZEJ infrastrukturze)

Do czasu playbooka wdrozeniowego (BE-SNAPSHOT, HOLD) sprzedajemy WYLACZNIE done-for-you:
marka klienta = nowy brand w naszym systemie (/brand_add, multi-brand LIVE), Tomasz operuje.
Model MVP rozwijany: rdzen dziala od dnia 1, funkcje doplywaja w cenie.

| Obiekt sprzedazowy | Status | Co klient dostaje DZIS | Co dojedzie w cenie |
|---|---|---|---|
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

## 4. BRAKI BLOKUJACE SPRZEDAZ (per przekroj)

1. Interfejs klienta = tylko Telegram (done-for-you to obchodzi: klient dostaje wyniki,
   opcjonalnie wlasny bot Telegram; self-service wymaga frontu webowego).
2. Wdrozenie = brak playbooka + intake 7 krokow (BE-SNAPSHOT HOLD).
3. Sprzedaz konkretnego agenta = sesja ofertowa z Managerem (gdy uruchomiony) z ta macierza.
