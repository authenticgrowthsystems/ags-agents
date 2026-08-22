# MIGRACJA DO SUPERGRUPY Z WĄTKAMI - plan kroku (22.08.2026)

**Zamówione przez Managera 22.08 jako osobny, opisany krok.** Warunek wstępny dla CM-PARTNER v1
(Telegram Topics). **Wymaga decyzji i ręki Tomasza** - bez przeniesienia rozmowy wątki nie istnieją.

**Nie zaczynamy tego przed porannym oknem bezpieczeństwa.** Kolejność ustalona: D-017, rotacje,
potem to.

---

## CO SIĘ NAPRAWDĘ ZMIENIA

**Jedna rzecz i z niej wynika cała reszta: `chat_id` czatu prywatnego jest INNY niż `chat_id`
supergrupy.** Telegram nadaje supergrupom identyfikatory ujemne, zwykle w postaci `-100...`.
Wszystko, co dziś adresuje wiadomości starą wartością, zamilknie - **i zamilknie po cichu**,
bo Telegram odpowie błędem, którego nikt nie czyta.

To jest dokładnie ten kształt awarii, na który mamy już dwa dowody z tego tygodnia: `/health`
mówiące `ok` przy martwym systemie (D-023) i `git pull` wyglądający na sukces przy złej gałęzi.
**Dlatego test ścieżki alarmu jest tu warunkiem odbioru, a nie dodatkiem.**

## MIEJSCA, GDZIE ŻYJE `chat_id` (policzone, nie oszacowane)

| gdzie | co trzyma | ile | co zrobić |
|---|---|---|---|
| `brand_config` klucz `admin_chat_ids` | **jedyne źródło adresu dla całego wyjścia proaktywnego** (`hitl.py:11-19` zwraca `arr[0]`) | 1 wiersz | **podmienić na nowy `chat_id` supergrupy** |
| `user_agent_state` | `chat_id` jako **klucz główny**, plus historia rozmów w `fsm_data.histories` | tyle wierszy, ile czatów | **NIE migrujemy.** Nowy czat zakłada nowy wiersz. Historia rozmowy zostaje w starym i tam ją zostawiamy - to nie jest dziennik, tylko kontekst krótkoterminowy |
| n8n, zapytania SQL kluczujące po `chat_id` | 4 zapytania (`:5720` zapis `active_agent`, `:5804`, `:5863`, `:6408` odczyty) | 4 | **nic** - biorą `chat_id` z wiadomości przychodzącej, więc same się dostosują |
| n8n, parametry węzłów | 148 wystąpień `chat_id` | 148 | **nic** - to `{{ }}` z wiadomości, nie literały. **Zweryfikować grepem, że NIE MA literału ze starym identyfikatorem** |
| `logbot` | ten sam `chat_id`, **inny bot** | 1 | **bot logowy musi zostać dodany do supergrupy osobno**, inaczej raporty zamilkną |

**Najważniejsze zdanie tej tabeli: migracja to podmiana JEDNEGO wiersza w `brand_config`.**
Reszta albo dostosowuje się sama, albo świadomie zostaje. Cała trudność leży nie w zmianie,
tylko w **sprawdzeniu, że nic nie zamilkło**.

---

## WARUNEK WSTEPNY: dwie poprawki w n8n, PRZED migracja

Obie sa jednolinijkowe i **musza wejsc w tym samym oknie n8n co D-017, przed przeniesieniem
rozmowy**. Po migracji ich brak objawi sie jako zepsute komendy w grupie, a objaw bedzie
mylacy: bot odpowie, tylko nie to, o co proszono.

1. **`Parse And Authorize Set`** - `reqText.trim().match(/^\/set\s+(\S+)\s+([\s\S]+)$/)`
   na `/^\/set(?:@\w+)?\s+(\S+)\s+([\s\S]+)$/`. Bez tego `/set@AGSbot klucz wartosc` dostaje
   odpowiedz "Format: /set <klucz> <wartosc>" na **poprawna** komende (D-028, czesc n8n).
2. **`Detect Update Type`** - dopisac `/anuluj` do listy przepustowej. Dzis go tam nie ma, wiec
   komenda nigdy nie dociera do Pythona, mimo ze trzy miejsca w kodzie ja obsluguja (D-029).

Strona cm-agenta jest juz naprawiona (siedem miejsc, `56d507e`), wiec zostaja wylacznie te dwie.

## PROCEDURA

### KROK 1 (Tomasz, Telegram): załóż supergrupę i włącz wątki

1. Nowa grupa, dodaj bota AGS **oraz bota logowego**.
2. Ustawienia grupy → **Topics** (wątki) → włącz.
3. Załóż dwa wątki: **Content** i **Sprzedaż**. Reszta dopiero po weryfikacji (decyzja Managera P2).
4. Nadaj botowi uprawnienia administratora - bez tego nie wyśle do wątku.

### KROK 2 (Tomasz): odczytaj identyfikatory

Napisz w **każdym** wątku dowolną wiadomość do bota, potem wklej mi log kontenera:

```bash
docker logs cm-agent --tail 40 | grep -i "chat_id\|thread"
```

Jeśli w logu tego nie widać, dodam tymczasowe wypisanie - **nie zgadujemy identyfikatorów**,
bo wpisany z palca zły numer da dokładnie tę cichą awarię, przed którą się zabezpieczamy.

### KROK 3 (BE): mapowanie w `brand_config`

Jeden wiersz `admin_chat_ids` na nowy identyfikator supergrupy plus nowy klucz z mapowaniem
`agent → wątek`. **Zero DDL.** Przygotuję gotowy SQL z bramką padającą zamkniętą, na wzór
`SQL_webhook_na_draft_19082026.sql`.

### KROK 4 (BE): kod - resolwer adresu

`hitl.cel(agent)` zwracające `{"chat_id", "message_thread_id"}`, 11 wołających plus trzy wyjścia
omijające `conversation._tg` (`hitl.py:92`, `logbot.py:33`, multipart w `matreview.py:38,57`).
Szczegóły w decyzji D1 specyfikacji.

### KROK 5: TEST ŚCIEŻKI ALARMU - warunek odbioru

**Nie „czy wiadomość doszła", tylko „czy system powie, gdy nie dojdzie".**

Trzy próby, każda ze **złym wsadem**, przed uznaniem migracji za zrobioną:

1. **Zły identyfikator wątku** dla jednego agenta → wiadomość ma **trafić do wątku głównego**
   i zostawić ślad w dzienniku, **nie zniknąć**. To jest zatwierdzone zachowanie z D1: brak
   wpisu pada w stronę działającego bota.
2. **Pusty `admin_chat_ids`** → system ma **powiedzieć, że nie ma dokąd pisać**, a nie ciągnąć
   dalej w ciszy.
3. **Bot usunięty z grupy** (albo bez uprawnień) → błąd Telegrama ma **wylądować w dzienniku
   z nazwą agenta i wątku**, a nie zostać połknięty.

### KROK 6: weryfikacja prawdziwą wiadomością w OBU wątkach

Decyzja Managera P2: reszta wątków dokładana **dopiero po tym**.

- **Content:** poproś o `/karty` w wątku Content - karta ma przyjść **tam**, nie w głównym.
- **Sprzedaż:** poproś o stan lejka w wątku Sprzedaż - ma przyjść **tam**.
- **Krzyżowo:** odprawa poranna ma trafić do Content, a przypomnienie sprzedażowe do Sprzedaży.
  **To jest właściwy test, bo to komunikaty tła** - a właśnie one nie mają dziś kontekstu agenta
  i to je trzeba było naprawić.

---

## CZEGO NIE ROBIMY

- **Nie migrujemy historii rozmów.** `fsm_data.histories` to kontekst krótkoterminowy, nie dziennik.
- **Nie zmieniamy klucza głównego `user_agent_state`** (decyzja D1, v1).
- **Nie kasujemy starego czatu** - zostaje jako droga odwrotu, dopóki oba wątki nie przejdą kroku 6.

## DROGA ODWROTU

Przywrócić stary `chat_id` w `admin_chat_ids`. **Jeden `UPDATE`.** Kod z resolwerem działa dalej,
bo brak mapowania wątku oznacza wysyłkę do czatu głównego - czyli dokładnie stare zachowanie.
Ta właściwość jest celowa i jest głównym powodem, dla którego D1 wybrał taką konstrukcję.
