# AP-307: Nowy kontrakt zbudowany bez przelaczenia ZYWEGO konsumenta starego

**Ustanowiony 20/07/2026 (BE, incydent publikacyjny P1).**
Pelny opis dopisany 11/08/2026 - do tego dnia AP-307 byl **jedynym anty-wzorcem w zakresie
306-315 bez wlasnego pliku**, mimo ze opisuje najdrozszy publicznie incydent tego projektu.
Blizniak AP-309: tam ta sama wada zyje w wielu miejscach naraz, tu **nowa droga powstaje obok
starej i nikt starej nie wylacza**.

## Wzorzec

Budujesz nowy mechanizm i on dziala. Testy przechodza, kod jest poprawny, sonda na nowej
sciezce zwraca to, czego oczekujesz. Tymczasem produkcja nadal chodzi **stara droga**, bo jeden
wiersz konfiguracji nigdy nie zostal przelaczony. Nowy kod nie jest zepsuty - jest **omijany**.

Zdanie, ktore to uruchamia, brzmi rozsadnie i padlo w tym projekcie doslownie:

> "jak cos dziala to po co to zmieniac jak budujesz cos innego" - Tomasz, 20/07

**Jest FALSZYWE dokladnie wtedy, gdy nowy build zmienia KONTRAKT, ktory stara droga konsumuje.**
Sloty przestaly byc dekoracja i staly sie obietnica. Jezyk przestal byc globalny i stal sie
wlasnoscia kanalu. Stara sciezka nie wie o zadnej z tych zmian i dalej robi swoje.

## Dowod: incydent publikacyjny 20/07/2026

Zbudowana byla cala maszyneria slotow - `humanize_slot`, serie z kolejnymi gniazdami, Scheduler
pytajacy `WHERE status='scheduled' AND scheduled_for <= NOW()`. **Wszystko poprawne.**
A `channels.config.publish_mode` dla AGS/x i AGS/linkedin nadal mialo wartosc `webhook`,
w ktorej `channels._delegate` strzela do adaptera n8n **natychmiast przy dispatchu** i sloty
ignoruje w calosci.

Cztery skutki jednego niezmienionego wiersza konfiguracji:

| skutek | co sie stalo |
|---|---|
| **burst** | 4-5 postow X w ciagu godziny zamiast rozproszenia; sloty 17:41-21:59 "opublikowane" okolo 15:00 |
| **zgubione media** | delegat przekazuje sam tekst, chunked-upload ma tylko sciezka Schedulera; wiersze 175-178, 181, 242, 246 mialy media i wyszly bez nich |
| **falszywy stan bazy** | callback publishera robil `UPDATE post_queue ... WHERE content_item_id=...` **bez id wiersza** - oznaczyl `published` WSZYSTKIE wiersze materialu, takze te ze slotami kilka godzin pozniej |
| **zly jezyk publicznie** | wariant powstal po polsku mimo `language_publish='en'`; wiersz 181 wyszedl po polsku na anglojezyczny profil LinkedIn |

## Why bad

- **Kazdy objaw wyglada na swiezy blad w NOWYM kodzie**, podczas gdy nowy kod jest poprawny
  i po prostu nieuzywany. Diagnoza zaczyna sie od czytania wlasciwego pliku i nie znajduje w nim nic.
- **Sfalszowany stan bazy zatruwa kazda pozniejsza diagnoze.** Wiersze oznaczone `published`
  ze slotami w przyszlosci sprawiaja, ze pozniejsze pytania o kolejke daja odpowiedzi bez sensu,
  a nikt nie wie, ktoremu wierszowi wierzyc.
- **Szkoda jest publiczna i natychmiastowa**, zanim ktokolwiek zdazy zareagowac: burst i obcy
  jezyk widza obserwujacy, nie tylko operator.
- Sonda "czy nowa sciezka dziala" **potwierdza sama siebie** - odpowiada na pytanie o kod,
  ktory wlasnie napisales, a nie o ten, ktory pobiegnie na produkcji.

## Correct

1. **Wypisz KAZDEGO zywego konsumenta zmienianego kontraktu** i przelacz albo zweryfikuj kazdego
   **w TYM SAMYM buildzie**. Tu byly dwa: `publish_mode` per kanal oraz callbacki publisherow.
2. **Zakoncz sonda END-TO-END przez sciezke, ktora naprawde pobiegnie na produkcji** - nie przez
   te, ktora wlasnie napisales. To jedyna sonda, ktora moze cie zaskoczyc.
3. **Zapytaj o konfiguracje, nie tylko o kod.** Kontrakt czesto zyje w wierszu bazy
   (`channels.config`), nie w pliku - a wtedy grep po repo pokaze zgodnosc, ktorej nie ma.
4. Gdy nowa droga wchodzi obok starej, **stara musi miec date wylaczenia albo jawny powod, dla
   ktorego zostaje**. "Zostawmy na wszelki wypadek" to wlasnie ten anty-wzorzec.

## Co z tego zyje DZISIAJ (stan 11/08/2026)

- **Oba kanaly AGS chodza na `publish_mode='post_queue'`** - publikuje Scheduler per slot wiersza,
  z mediami. Tryb `draft` (gotowce do recznej wklejki) zostaje dostepny per kanal.
- **`webhook` jest zabroniony** - `docs/komponenty/kolejka-publikacja.md` mowi wprost "nie uzywac".
- **UZBROJONA MINA, swiadomie niezalatana:** callback per-wiersz nadal oznacza `published`
  wszystkie wiersze materialu. Adaptery po przelaczeniu trybow sa nieuzywane, wiec dzis to nie boli -
  ale **powrot do trybu `webhook` bez wczesniejszej naprawy callbacku odtworzy skutek numer trzy
  co do znaku**. To jest warunek twardy, nie sugestia.
- **STRAZNIK JEZYKA** w `channels.stage_variant`: kanal EN plus tekst wygladajacy na polski
  = tlumaczenie PRZED zapisem do kolejki, zeby karta HITL pokazywala to, co naprawde wyjdzie.
  Od 11/08 to tlumaczenie wie, ze publikuje (`do_publikacji=True`) i przechodzi kontrole wiernosci.

## Lekcja z 11/08: zapisany anty-wzorzec nie jest wdrozonym anty-wzorcem

`DEPLOY_CHECKLIST.md` - playbook instalacji produktu u klienta - **przez trzy tygodnie po tym
incydencie nadal instruowal, zeby ustawic `publish_mode` na `webhook`**. Anty-wzorzec byl
zapisany, komponent poprawiony, produkcja przelaczona, a dokument, ktory ktos WYKONA krok
po kroku u nowego klienta, kazal odtworzyc dokladnie te awarie.

Znalezione dopiero przy przegladzie gotowosci repo 11/08 i poprawione w wersji v3.

**Wniosek szerszy niz sam AP-307:** po zapisaniu anty-wzorca sprawdz, czy jakikolwiek dokument
instruktazowy nadal uczy starego zachowania. Kod poprawiles, bo pamietasz, gdzie mieszka.
Instrukcje sa w innym miejscu i nikt ich nie kompiluje.

## Punkty zaczepienia

- `docs/ops/INCYDENT_PUBLIKACJI_20072026.md` - pelny raport z sondami i numerami wierszy
- `docs/ops/incydent_publikacji_20072026.sql` - paczka naprawcza (A-G)
- `docs/komponenty/kolejka-publikacja.md` - tryby publikacji per kanal, straznik jezyka, mina callbacku
- `DEPLOY_CHECKLIST.md` v3 - poprawiona instrukcja instalacji
- `anti-patterns/library.md` - wpis skrocony + indeks 306-315
