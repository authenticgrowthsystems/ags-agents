# Komponent: KARTY MATERIALOW + APPROVAL HITL (przeglad i zatwierdzanie)

**STATUS GOTOWOSCI: KOMPLETNY** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Dwa widoki decyzyjne w Telegramie:

1. **Karty matreview** (przeglad materialow KARTAMI, nie floodem): jedna karta
   na material, nawigacja guzikami, decyzje ok/no, edycja, media, pelna tresc.
   Callbacki `matnav:*` -> n8n -> `POST /matnav` -> `matreview.handle`.
2. **Wiadomosc approval** (`hitl.send_approval`): material 'needs_approval'
   z wariantami per kanal + guziki `cm:<id>:approve|reject` + guziki formatu
   [Jeden post/Seria/Artykul]. DECYZJA ZAPADA TUTAJ - dlatego ostrzezenia
   (np. ⚠️ DUPLIKACJA) musza byc w OBU widokach.

## Wejscia-wyjscia i tabele

- `content_items`: statusy draft/brief -> needs_approval -> approved/rejected;
  `media` jsonb (grafiki, image_prompt, dup_warning, review_copy).
- `post_queue`: odrzucenie karty ('no') przelacza wiersze materialu na 'rejected'.
- `agent_learning_log`: KAZDA decyzja na karcie/edycji/podmianie -> wpis
  (accepted/edited/rejected/replaced); generacja czyta ostatnie 20
  (`generate._learning_digest`) - edycja = akceptacja + nauka stylu.

## Funkcje kart (stan v9+)

- Widoki: kompakt/rozwin, filtr dnia, filtr "tylko z mediami"; karta wszystkich
  marek z tagiem 🏷; karta approved/handed_off/published = view-only 🔒
  (`handed_off` do 03/08/2026 nazywalo sie `dispatching` - D-008; etykieta
  widoczna dla czlowieka to "ROZESLANY DO KOLEJKI" plus liczba wierszy
  oczekujacych i ich terminy - D-006).
- GODZINA PUBLIKACJI NA KARCIE (od 19/08/2026, domkniecie dlugu D-015): linia
  `🕐` pokazuje godzine, o ktorej material NAPRAWDE wyjdzie, czyli
  **`max(slot planu, czas kolejki)`** - te sama liczbe, co meldunek bota
  "CM przydzielil slot". Do 19/08 karta czytala sam `content_items.scheduled_for`,
  czyli CZYSTY SLOT PLANU, wiec przy kolejce wypadajacej pozniej obiecywala
  godzine do 15 minut za wczesnie. Tomasz widzial wtedy dwie rozne liczby dla
  jednego posta i musial zgadywac, ktora obowiazuje (AP-312 w wydaniu liczbowym).
  Regula NIE jest tu przepisana drugi raz: `matreview._godzina_karty` wola
  `worker._godzina_publikacji`, czyli ten sam kod, co meldunek (AP-309).
  Ta sama liczba steruje naglowkiem dnia (DZIS/JUTRO) i ostrzezeniem "SLOT MINAL",
  a takze paragonem po edycji i po "✅⏭ Na koniec kolejki" oraz karta podgladu 🔒.
- GDY KOLEJKI JESZCZE NIE MA, KARTA MOWI, ZE NIE WIE. Material bywa ogladany
  przed wysylka i wtedy wiersza kolejki nie ma, wiec dokladnej godziny NIE MA.
  Karta pisze slot planu z dopiskiem "planowo (dokladnej nie znam - brak wpisu
  w kolejce; realna wypadnie do 15 minut pozniej)". Przedzial jest znany (bramka
  `claim_item` od dolu, `humanize_slot` +15 min od gory), sama godzina nie - i tak
  ma to brzmiec, bo domysl zapisany jak fakt jest gorszy niz brak danych (AP-317).
  Odczyt: `matreview._czas_kolejki`, JEDNO zapytanie na karte (wzorzec
  `_stan_rozsylki` z D-006, nie N+1).
  Test: `cm-agent/tests/test_godzina_na_karcie.py`.
- Guziki intake przy zapisie materialu: Kolejka / Teraz / Odrzuc
  (`send_intake_buttons`).
- 🎨 Generuj (grafika na zadanie), ➕ Media (dolaczenie zdjecia; galeria tylko
  na zadanie `mgal` - bez floodu), 📋 Prompt (wysyla pelny prompt graficzny
  z `media[].image_prompt` do skopiowania w zewnetrzny generator).
- 📄 Pokaz pelna tresc: kawalki ~3900 znakow (ciecie na granicy akapitu);
  [ARTYKUL] i tresci >3900 dodatkowo jako plik .md (`_tg_send_document`).
  W approval: kazdy wariant >3500 znakow leci dodatkowo jako plik .md.
- Edycja ('edytuj' -> `apply_edit`): zapis final_content + destylacja regul
  stylu (`_distill_style_rules`) + wpis learning_log.
  **Destylacja WYLACZONA od 19/08 (D-019)**: zwraca pusto, wiec paragon nie ma juz
  linii "📚 Wyuczone z tej korekty" - i dobrze, bo nauki nie ma. Wpis do learning_log
  i zapis final_content zostaja bez zmian. Szczegoly: [glos-marki.md](glos-marki.md).
- Inny kat: `apply_angle_guidance` - regeneracja z wytyczna; czysci stare
  dup_warning.
- Po KAZDEJ decyzji: paragon NOWA wiadomoscia + nastepna karta NOWA wiadomoscia
  NA DOLE czatu (card_bottom - koniec przewijania w gore).
- Tryb reczny w approval pokazuje tekst-matke (canonical), nie pusty skrot.
- ⚠️ INTERPUNKCJA (24/07, paczka #1 Managera pkt 8): dla marek polskojezycznych
  (brand_id TNM / RDC) karta pokazuje miejsca, w ktorych prawdopodobnie brakuje
  przecinka przed spojnikiem podrzednym (ze, zeby, ktory, gdy, jesli, bo).
  To FLAGA dla czlowieka, nie blokada i nie automatyczna poprawka: heurystyka jest
  deterministyczna (zero LLM, zero kosztu), liczona z PELNEJ tresci, max 3 fragmenty.
  Poczatek zdania, istniejacy przecinek i zbitki typu "mimo ze" / "w ktorym" nie sa
  zglaszane (`compliance.pl_comma_flags`, testy: cm-agent/tests/test_paczka1.py).

## Konfiguracja

- `brand_config`: `cm_auto_image` (auto-grafika przed karta), `admin_chat_ids`.
- Przepustka komend w n8n Detect Update Type: /karty /schowek /decyzje /brand*
  ida do cm-agenta (nie gina w routerze).

## Punkty zaczepienia w kodzie

- `cm-agent/app/compliance.py`: `pl_comma_flags` (heurystyka interpunkcji PL, flaga).
- `cm-agent/app/matreview.py`: `_card` (render karty, w tym linie ⚠️ DUPLIKACJA
  i ⚠️ INTERPUNKCJA), `_czas_kolejki` + `_godzina_karty` (godzina publikacji,
  D-015), `_view_card` (podglad 🔒),
  `send_review_card`, `handle` (callbacki matnav, akcje ok/no/okq/fulltext),
  `send_intake_buttons`, `apply_edit`, `apply_angle_guidance`,
  `_distill_style_rules`, `log_learning`, `_tg_send_document`,
  `media_attach_watch` (➕ Media), `resend_intake`.
- `cm-agent/app/hitl.py`: `send_approval` (wiadomosc approval + guziki + pliki
  .md + dup_warning).
- `cm-agent/app/worker.py`: endpoint `POST /matnav`; guziki formatu synthesis
  w HITL n8n.
- Rozmowa CM: `show_review_cards` (karta po fragmencie tematu, takze approved).

## Kanony ktore go dotycza

- Decyzje Tomasza = GUZIKI; paragon KAZDEJ decyzji nowa wiadomoscia (05/07).
- Edycja = akceptacja + nauka (kanon UX 05/07).
- Zatwierdzanie TRESCI nigdy nie przechodzi na semi-auto (kanon 19/07).
- Ostrzezenie musi byc w widoku, w ktorym zapada decyzja (lekcja 20/07).

## Zmiany 22/07 (uwagi Tomasza 00:03)

- Wiadomosc zatwierdzenia (hitl.send_approval) POKAZUJE kopie PL (media kind='review_pl',
  sekcja "Odpowiednik do przegladu") - wczesniej byla tylko na kartach przegladu,
  a decyzja zapada na approval.
- Klawiatura approval ma guziki grafiki: "Generuj grafike" (matnav:gen) i "Dopnij zdjecie"
  (matnav:madd) - te same akcje co na kartach, obraz dopina sie do materialu I wierszy kolejki.
- Straznik preambuly (generate._strip_meta_preamble): meta-komentarz modelu przed '---'
  ("I've reviewed the canonical...") jest ucinany z wariantu przed stagingiem
  (incydent: wiersz 280 poszedl do kolejki z preambula w tresci).

## Znane pulapki

- BUG matnav unpack (od v7, naprawiony 12/07): rozpakowanie `_card()` do 2
  wartosci wybuchalo PO zapisie statusu - objaw "kliknalem odrzuc i nic".
- n8n POLYKAL /karty (router komend) - naprawione przepustka; nowa komenda
  tekstowa wymaga sprawdzenia routera (patrz n8n-transport.md).
- Karta approved jest view-only - zmiana tresci po approve wymaga podmiany
  materialu (replace_material), nie edycji karty.
- Odrzucenie na etapie intake (matdec:drop, status draft) NIE dotyka pq -
  materialy draft nie maja jeszcze wierszy pq (celowe).
