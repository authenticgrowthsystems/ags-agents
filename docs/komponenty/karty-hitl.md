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
  marek z tagiem 🏷; karta approved/dispatching/published = view-only 🔒.
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
- Inny kat: `apply_angle_guidance` - regeneracja z wytyczna; czysci stare
  dup_warning.
- Po KAZDEJ decyzji: paragon NOWA wiadomoscia + nastepna karta NOWA wiadomoscia
  NA DOLE czatu (card_bottom - koniec przewijania w gore).
- Tryb reczny w approval pokazuje tekst-matke (canonical), nie pusty skrot.

## Konfiguracja

- `brand_config`: `cm_auto_image` (auto-grafika przed karta), `admin_chat_ids`.
- Przepustka komend w n8n Detect Update Type: /karty /schowek /decyzje /brand*
  ida do cm-agenta (nie gina w routerze).

## Punkty zaczepienia w kodzie

- `cm-agent/app/matreview.py`: `_card` (render karty, w tym linia ⚠️ DUPLIKACJA),
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

## Znane pulapki

- BUG matnav unpack (od v7, naprawiony 12/07): rozpakowanie `_card()` do 2
  wartosci wybuchalo PO zapisie statusu - objaw "kliknalem odrzuc i nic".
- n8n POLYKAL /karty (router komend) - naprawione przepustka; nowa komenda
  tekstowa wymaga sprawdzenia routera (patrz n8n-transport.md).
- Karta approved jest view-only - zmiana tresci po approve wymaga podmiany
  materialu (replace_material), nie edycji karty.
- Odrzucenie na etapie intake (matdec:drop, status draft) NIE dotyka pq -
  materialy draft nie maja jeszcze wierszy pq (celowe).
