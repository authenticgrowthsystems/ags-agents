# INCYDENT PUBLIKACJI 20/07/2026 (P1) - raport i naprawa

Zgloszenie Tomasza (20/07 popoludnie): (1) X opublikowal 4-5 postow w ciagu
jednej godziny zamiast rozproszenia na caly dzien, (2) ZADNA grafika nie
wyszla na X mimo dolaczonych mediow, (3) LinkedIn (profil prywatny, kanal
EN-only) opublikowal post PO POLSKU.

## Przyczyna zrodlowa (udowodniona)

`channels.config.publish_mode='webhook'` dla AGS/x ORAZ AGS/linkedin.
W tym trybie `channels._delegate` strzela do adaptera n8n NATYCHMIAST przy
dispatchu zatwierdzonego materialu - sloty post_queue sa ignorowane.
Trzy skutki:

1. **Burst**: wszystkie wiersze materialu wychodzily w chwili zatwierdzenia,
   nie w swoich slotach (sloty 17:41-21:59 "opublikowane" ~15:00).
2. **Zgubione media**: delegat przekazuje content bez chunked-upload mediow;
   sciezka Schedulera MA upload mediow (OAuth1 chunked). Sonda: wiersze
   175/176/177/178/181/242/246 mialy media z file_id - nie wyszly.
3. **Falszywy stan bazy**: callback Subagent X Publisher robi
   `UPDATE post_queue ... WHERE content_item_id=... AND status<>'published'`
   (bez id wiersza) - oznaczal 'published' WSZYSTKIE wiersze materialu.
4. **Polski na LinkedIn**: wariant wygenerowal sie po polsku mimo
   `language_publish='en'` (generacja nie miala twardego straznika jezyka),
   wiersz 181 wyszedl po polsku na profil.

Scheduler (`WHERE status='scheduled' AND scheduled_for <= NOW()`) byl
POPRAWNY, tylko omijany. Kod slotow (humanize_slot, serie) byl POPRAWNY,
tylko jego wyniki ladowaly w sciezce, ktora ich nie czyta. Anti-pattern:
AP-307 w anti-patterns/library.md.

## Naprawa (paczka: docs/ops/incydent_publikacji_20072026.sql)

- A) AGS/x -> `publish_mode='post_queue'`: publikuje Scheduler per slot
  wiersza, z mediami.
- B) AGS/linkedin -> `publish_mode='draft'`: gotowce reczne (Scheduler nie
  publikuje LinkedIn; adapter LinkedIn ignorowal sloty).
- C) Callback per-row NIE naprawiany dzis (adaptery po A+B nieuzywane) -
  BACKLOG z twardym warunkiem: naprawa PRZED jakimkolwiek powrotem webhook.
- D) 10 polskich wierszy kolejki X (182-185, 210-215) przetlumaczone na EN
  przez BE (Tomasz zatwierdzil SENS po polsku; karta kontrolna:
  docs/ops/TLUMACZENIA_EN_20072026.md; wykonanie SQL = zatwierdzenie).
- E) Re-slot wierszy z martwymi slotami z 19/07: 246 -> 23/07 19:12,
  247 -> 23/07 20:23, 248 -> 24/07 17:42 (material dispatchuje sie 23/07 18:45,
  sloty wierszy musza byc POZNIEJSZE - zlapane sonda przed wykonaniem).
- F) Sonda przed wykonaniem (20/07 ~22:15): zero held/scheduled, wszystkie wiersze
  'review', materialy 'approved' z przyszlymi slotami - freeze niepotrzebny,
  w SQL zostal tylko bezpiecznik held->review.
- G) Kod: STRAZNIK JEZYKA w `channels.stage_variant` (kanal 'en' + tekst
  po polsku -> translate_text przed zapisem; karta HITL pokazuje finalna
  tresc). Wchodzi z wieczornym rebuildem cm-agent.

Opublikowanego polskiego posta na LinkedIn NIE zdejmujemy (rekomendacja
przyjeta: ~70% obserwujacych to Polacy, usuwanie robi wiecej szumu).

## Zapobieganie

- AP-307: zmiana kontraktu = przelaczenie/weryfikacja KAZDEGO zywego
  konsumenta w tym samym buildzie + sonda end-to-end przez sciezke
  produkcyjna.
- Dokumentacja komponentu kolejka-publikacja.md zaktualizowana w TYM SAMYM
  commicie (tryby per kanal, straznik jezyka, mina callbacku).
