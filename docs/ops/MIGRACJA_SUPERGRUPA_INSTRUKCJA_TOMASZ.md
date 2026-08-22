# Migracja bota do supergrupy - instrukcja klik po kliku

**Dla Tomasza. Jutrzejsze okno, PO rotacjach.** Plan techniczny: `docs/ops/MIGRACJA_SUPERGRUPA.md`
(ten dokument jest jego wykonawczą wersją, nie duplikatem - tam jest „dlaczego", tu „co kliknąć").

Czas: około 15 minut. Potrzebujesz **telefonu albo Telegrama na komputerze** oraz **terminala
na Mikrusie**.

---

## ZANIM ZACZNIESZ - dwie rzeczy, które musisz wiedzieć

**1. Po migracji przez pewien czas wszystko będzie lądować w wątku głównym.** To NIE jest usterka.
Kierowanie do wątków tematycznych dokłada kod z bloku CM-PARTNER, który budujemy po tym oknie.
Migracja jest warunkiem wstępnym, nie efektem końcowym.

**2. Stary czat prywatny zostaje nietknięty jako droga odwrotu.** Nic z niego nie kasujemy,
dopóki oba wątki nie przejdą testu.

---

## KROK 1: załóż grupę

1. Telegram → **Nowa grupa**.
2. Nazwa: **AGS** (albo jak wolisz, nazwa nie ma znaczenia technicznego).
3. Dodaj **oba boty**: głównego bota AGS **oraz bota logowego**.
   Jeśli Telegram nie pozwala dodać bota przy zakładaniu, załóż grupę z samym sobą i dodaj boty
   zaraz potem przez **Dodaj członków**.
4. Utwórz grupę.

**Warunek przejścia dalej:** w grupie widzisz oba boty na liście członków.
Jeśli któregoś nie ma, zatrzymaj się.

## KROK 2: zamień grupę w supergrupę z wątkami

1. Wejdź w **nazwę grupy** na górze → **Edytuj** (ikona ołówka).
2. Znajdź przełącznik **Tematy** (po angielsku **Topics**) i **włącz go**.
3. Zatwierdź.

Telegram sam zamieni grupę w supergrupę. **To jest moment, w którym zmienia się identyfikator
czatu** - dlatego wszystko poniżej robimy po tym kroku, nie przed.

**Warunek przejścia dalej:** widok grupy zmienił się na listę tematów.
Jeśli przełącznika **Tematy** nie ma, grupa jest za mała albo nie jesteś jej właścicielem -
zatrzymaj się i napisz.

## KROK 3: załóż dwa wątki

Dokładnie dwa, ani jednego więcej (decyzja Managera: reszta po weryfikacji).

1. **Content**
2. **Sprzedaż**

## KROK 4: nadaj botowi uprawnienia administratora

1. Nazwa grupy → **Administratorzy** → **Dodaj administratora** → wybierz **głównego bota AGS**.
2. Włącz mu uprawnienia:
   - **Wysyłanie wiadomości**
   - **Zarządzanie tematami**
   - **Przypinanie wiadomości**
3. Zatwierdź. **Bota logowego wystarczy zostawić zwykłym członkiem.**

Bez „Zarządzania tematami" bot nie wyśle nic do wątku i **nie powie, dlaczego**.

## KROK 5: WYŁĄCZ TRYB PRYWATNOŚCI BOTA - to jest krok, który najłatwiej pominąć

**Bez tego bot w grupie zobaczy WYŁĄCZNIE komendy zaczynające się od ukośnika, a każdą zwykłą
wiadomość zignoruje.** Cała rozmowa z CM przestanie działać, a bot nie zgłosi żadnego błędu -
po prostu przestanie odpowiadać na to, co piszesz normalnym zdaniem.

1. Napisz do **@BotFather**.
2. Wyślij: `/mybots`
3. Wybierz głównego bota AGS.
4. **Bot Settings** → **Group Privacy**.
5. Jeśli widnieje **enabled**, kliknij **Turn off**.

**Warunek przejścia dalej:** BotFather potwierdza `Privacy mode is disabled`.
To jest jedyny krok w tej instrukcji, którego pominięcie da awarię wyglądającą jak kaprys bota.

## KROK 6: powiedz coś w każdym wątku

Napisz **w wątku Content** oraz **w wątku Sprzedaż** dowolne zdanie, na przykład `test`.

Bot najprawdopodobniej nie odpowie i **tak ma być** - nie zna jeszcze tej grupy. Chodzi o to,
żeby wiadomości pojawiły się w logu i żebym mógł odczytać identyfikatory.

Potem wklej mi wynik:

```bash
docker logs cm-agent --tail 60 | grep -i "chat_id\|thread\|message"
```

**Nie zgadujemy identyfikatorów.** Zły numer wpisany z palca daje dokładnie tę cichą awarię,
przed którą się tu zabezpieczamy.

## KROK 7: podmiana adresu - moja robota

Przygotuję gotowy SQL z bramką padającą zamkniętą. Ty go tylko wkleisz, tak jak przy oknie 19/08.
**To jest podmiana jednego wiersza w konfiguracji.**

## KROK 8: TEST ŚCIEŻKI ALARMU - warunek odbioru, nie formalność

Sprawdzamy nie to, czy wiadomość doszła, ale **czy system powie, gdy nie dojdzie**.
Poprowadzę Cię przez trzy próby ze złym wsadem. Każda ma coś zepsuć na chwilę i pokazać,
że system to zgłasza zamiast milczeć.

## KROK 9: weryfikacja prawdziwą wiadomością

- w wątku **Content** poproś o `/karty` - karta ma przyjść **tam**;
- w wątku **Sprzedaż** poproś o stan lejka - ma przyjść **tam**;
- odprawa poranna następnego dnia ma trafić do **Content**.

---

## CHECKLISTA - odhacz przed uznaniem migracji za zrobioną

| # | co | kto | zrobione |
|---|---|---|---|
| 1 | grupa założona, **oba** boty w środku | Tomasz | ☐ |
| 2 | **Tematy** włączone, grupa jest supergrupą | Tomasz | ☐ |
| 3 | dwa wątki: Content i Sprzedaż | Tomasz | ☐ |
| 4 | główny bot administratorem, ma **Zarządzanie tematami** | Tomasz | ☐ |
| 5 | **Group Privacy = disabled** w BotFather | Tomasz | ☐ |
| 6 | identyfikaty odczytane **z logu**, nie zgadnięte | Tomasz + BE | ☐ |
| 7 | `admin_chat_ids` podmienione, mapowanie wątków zapisane | BE | ☐ |
| 8 | **próba 1:** zły identyfikator wątku → wiadomość trafia do wątku głównego i zostawia ślad, **nie znika** | BE + Tomasz | ☐ |
| 9 | **próba 2:** pusty `admin_chat_ids` → system **mówi**, że nie ma dokąd pisać | BE + Tomasz | ☐ |
| 10 | **próba 3:** bot bez uprawnień → błąd Telegrama **ląduje w dzienniku** z nazwą agenta, nie zostaje połknięty | BE + Tomasz | ☐ |
| 11 | `/karty` w wątku Content przychodzi **tam** | Tomasz | ☐ |
| 12 | stan lejka w wątku Sprzedaż przychodzi **tam** | Tomasz | ☐ |
| 13 | **bot logowy** odzywa się w grupie (raport dzienny) | Tomasz | ☐ |
| 14 | stary czat prywatny **nietknięty** jako droga odwrotu | - | ☐ |

**Dopóki punkty 8, 9 i 10 nie są odhaczone, migracja nie jest zrobiona** - jest tylko
przeprowadzona. To rozróżnienie kosztowało nas w tym tygodniu dwa razy: `/health` mówiące `ok`
przy martwym systemie i `git pull` wyglądający na sukces przy złej gałęzi.

---

## DROGA ODWROTU

Jeden `UPDATE` przywracający stary identyfikator czatu. Kod działa dalej bez zmian, bo brak
mapowania wątku oznacza wysyłkę do czatu głównego - czyli dokładnie stare zachowanie.
**Ta właściwość jest celowa i to główny powód, dla którego zaprojektowaliśmy to w ten sposób.**
