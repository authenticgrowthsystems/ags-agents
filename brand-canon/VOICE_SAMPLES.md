# AGS Voice Samples & Notes (pamięć stylu pisania)

**Cel:** żywa pamięć agenta o tym, JAK Tomasz naprawdę pisze. Za każdym razem, gdy Tomasz edytuje wygenerowany draft i oznaczy go, jego poprawiona wersja zapisuje się tutaj jako PRÓBKA głosu i wraca do każdej kolejnej generacji jako przykład (few-shot).

**Kanoniczny magazyn:** tabele Postgres `voice_samples` (Twoje poprawione przykłady) i `voice_notes` (reguły narracji) na bazie bota AGS. Ten plik to czytelne okno na nie. Żywe dane siedzą w bazie, bo agent n8n czyta je w momencie generacji (nie sięgnie pliku na Twoim dysku).

## Jak powstaje próbka
1. Pomysł → "Zrób post" → draft generuje się w PL + EN.
2. Klikasz "Edytuj", wysyłasz swoją poprawioną wersję po polsku.
3. Bot re-synchronizuje angielski i pokazuje obie wersje ponownie, z guzikiem "To próbka mojego głosu".
4. Klikasz → Twoja edycja (PL/EN) zapisuje się do `voice_samples` → każdy kolejny post lepiej trafia w Twój głos.

## Aktywne reguły głosu (tabela `voice_notes`)
1. Gdy na zdjęciu jest widoczny tekst (napis, podpis, etykieta), użyj tego słowa lub frazy jako kreatywnej kotwicy posta.
2. Sięgaj po metaforę taniec = architektura: najpierw fundamenty i konkretny szlif, dopiero potem freestyle i żonglowanie. Freestyle'ować można tylko jak masz czym, nigdy z niczego.

## Próbki
(jeszcze brak - pojawią się tutaj, gdy oznaczysz swoje edycje)

---
Plik odświeżam z bazy na żądanie ("odśwież próbki głosu").
