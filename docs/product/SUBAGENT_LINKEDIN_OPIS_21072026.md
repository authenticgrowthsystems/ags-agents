# SUBAGENT LINKEDIN - pelny opis stanowiska i stanu (AKTUALIZACJA 22/07/2026 ~17:45)

Blizniak Subagenta X (te same warstwy, baza, kontrakt 8 obowiazkow - czytaj
SUBAGENT_X_OPIS_21072026.md; tu tylko ROZNICE). REZIM STABILIZACJI jak X.

## 0. Specyfika platformy

Sukces LinkedIn = komentarze w pierwszych 60-90 min + czas czytania. Kadencja: pon-pt
1 post (okno profilu ok. 16:00-18:00), sobota nic, NIEDZIELA ARTYKUL - robi TOMASZ
RECZNIE na podkladzie "CM czyta swiat" (dowod sobotni 26/07). Profil prywatny publikuje
WYLACZNIE PO ANGIELSKU (straznik jezyka w stagingu).

## 1. ZROBIONE (stan LIVE 22/07 ~17:45)

| Obowiazek | Co dziala | Jak zrealizowane |
|---|---|---|
| O1 Publikacja **AUTOMATYCZNA** | od 22/07 ~17:40 LinkedIn publikuje SCHEDULER per slot wiersza (kanon: zatwierdzone publikuje sie ZAWSZE): galaz Route Platform -> Publish To LinkedIn (registerUpload obrazu -> PUT -> ugcPosts; kod 1:1 z Publishera, ktory publikowal z obrazem 20/07) -> ksiega per-wiersz -> potwierdzenie na Telegram. PIERWSZY ZYWY DOWOD: wiersz 205, 22/07 18:12 | n8n: Scheduler (patch scheduler-linkedin-branch-22072026.cjs); publish_mode='post_queue' |
| O1 Gotowiec (fallback) | tryb 'draft' per kanal ZOSTAJE dostepny: pelny zestaw (tekst+grafika) do rozmowy + domkniecie `wklejone <id>`; uzywany np. dla [ARTYKUL] (API nie publikuje artykulow) | Python: worker._send_manual_paste_kits + route |
| O2 Tworzenie | jak X (Voice Bible, TRUTH_GUARD, straznik jezyka EN, straznik preambuly, dedup) + kopia PL do przegladu na karcie zatwierdzenia | wspolne organy |
| O3 Komentarze/DM | comment-radar per autor, rozpoznanie DM vs post, odpowiedz w jezyku rozmowcy, 1 tap [Wyslalem] domyka cykl + stadium CRM | wspolne organy (INTAKE-UX) |
| O5 Metryki | import xlsx (AggregateAnalytics przez Telegram) + PROFIL w raportach; kolektor API GOTOWY w kodzie - czeka WYLACZNIE na scope po review App 2 CMA | Python: metrics_import; n8n: document_xlsx |
| O6 Relacje | wspolny CRM (intake, stadium, obowiazek klasyfikacji z raportow pracy); zywe dowody 21-22/07: Djordje (DM-cykl domkniety), Neil Patel, seed Crystalee/Chris/Jay | wspolne organy |
| O8 Rozmowa + Lacznik | jak X; masterprompt czatowy LINKEDIN_AGS_v1 (praca na abonamencie -> RAPORT PRACY; stan gry z Notion) | docs/product/masterprompty-czat/ |

## 2. DO ZROBIENIA (backlog - stabilizacja blokuje nowe funkcje)

| Brak | Status |
|---|---|
| Dowod 48h bez interwencji (w tym pierwsze auto-posty 205 i 280) | OBSERWACJA |
| Scope metryk API (memberCreatorPostAnalytics) | App 2 CMA - poza nasza kontrola |
| Strony firmowe AGS/TNM/RDC + routing multi-konto | po CMA |
| Karuzele/dokumenty PDF (najwyzszy dwell time) | backlog |
| Token OAuth profilu wygasa ~01/09/2026 | ODNOWIC PRZED - pilnowac |

## 3. Recepta na kolejne kanaly (IG, FB, TikTok, YT)

Nowy subagent = wiersz w channels (menu /agents samo go widzi) + galaz publikacji
w Schedulerze ALBO tryb gotowca od dnia 1 + taktyka platformy w konfiguracji +
metryki (kolektor per API albo import pliku). Plan, karty, CRM, decyzje, nauka,
raporty, rozmowa, Lacznik - WSPOLNE ORGANY za darmo. Dowod recepty: galaz LinkedIn
w Schedulerze powstala w jeden wieczor, bo caly kregoslup juz istnial.
