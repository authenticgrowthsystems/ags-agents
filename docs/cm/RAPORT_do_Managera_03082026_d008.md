# RAPORT do Managera: D-008 wdrozone (03/08/2026)

**Od:** osobna instancja Claude Code (build wg `docs/briefs/BRIEF_D008_przemianowanie_dispatching.md`).
**Stan:** wdrozone na produkcji, okno 19:28:30-19:42 UTC. Zero utraconych publikacji.

`content_items.status` nie nazywa sie juz `dispatching`. Nazywa sie **`handed_off`** i mowi to samo,
co etykieta wdrozona przy D-006: "ROZESLANY DO KOLEJKI".

---

## 1. Nazwa: dlaczego nie ta z wpisu w dlugu

Wpis proponowal `w_kolejce`, `rozeslane`, `czeka_na_sloty`. Brief rekomendowal `rozeslane`.
Tomasz wybral **`handed_off`** i mial racje z powodu, ktorego nie widzial ani wpis, ani brief:

**stan nie konczy sie publikacja.** `worker._DISPATCH_OK` zawiera `held` - czyli gotowiec do
RECZNEJ wklejki. Przy LinkedInie material wychodzi z tego stanu po kilkudziesieciu sekundach,
a publikacja dopiero czeka na czlowieka. Kazda nazwa obiecujaca publikacje (`awaiting_publication`
i podobne) odtworzylaby **AP-312 wewnatrz poprawki na AP-312**.

`handed_off` to slowo, ktore kodebaza wybrala sama, zanim ktokolwiek przemianowal wartosc:
*"dispatch = HAND-OFF, nie publikacja"* (`worker.py`), *"Every mode here just HANDS OFF"*
(`channels.py`).

## 2. Cztery ustalenia, ktore rozjechaly sie z briefem i z wpisem w dlugu

**(a) Inwentarz "32 miejsca" mieszal DWA ROZLACZNE SLOWNIKI.** Do materialu nalezalo **20**
trafien, do `post_queue` **11**, jedno bylo neutralnym komentarzem. `post_queue.status` ma
WLASNA wartosc `dispatching` i znaczy ona co innego: jeden wiersz kolejki oddany subagentowi.
Przeniesienie wszystkich 32 zerwaloby dopasowanie w kolejce publikacji.

**(b) Zywy wezel n8n ma OBIE wartosci w JEDNYM zapytaniu.** `AGS Scheduler v1`, wezly
`Mark Published` i `Mark Published LI`:

```sql
UPDATE content_items ci SET status='published'
WHERE ci.status='dispatching'                                          -- zmienione
  AND NOT EXISTS (SELECT 1 FROM post_queue q WHERE ...
        AND q.status IN ('review','scheduled','queued','dispatching')); -- zostawione
```

Podmiana "po calym tekscie" nie dalaby zadnego bledu - SQL nadal bylby poprawny.

**(c) Pisarzy do `content_items` jest TRZECH, nie jeden.** Poza `cm-agentem` pisza tam
`AGS Scheduler v1` (cron co minute) i `AGS HITL Handler v1.0` (wezel `Cm Resolve Gate`,
guziki bota, z pominieciem cm-agenta). **Trzeci umknal wszystkim wczesniejszym odczytom, bo
nie zawiera slowa `dispatching`** - trzeba bylo szukac nazwy TABELI, nie wartosci. To jest
AP-309 od strony szukania, w czystej postaci.

**(d) Migracja danych okazala sie ZEROWA.** Odczyt przy stojacych pisarzach: zero wierszy
w starej wartosci. Siedem materialow z 27/07 przez tydzien dopublikowalo swoje serie.
Wpis w dlugu opisywal stan sprzed tygodnia - jak D-003 i D-011.

## 3. Bramka bezpieczenstwa nie zadzialala za pierwszym razem

Najwazniejsza lekcja z tego okna, wpisana do runbooka jako **punkt 10**.

`psql` **nie podstawia zmiennych `:nazwa` wewnatrz bloku cytowanego dolarami** (`DO $$ ... $$`).
Bramka na liczbie wierszy wywalila sie skladniowo, zanim cokolwiek sprawdzila:

```
ERROR:  syntax error at or near ":"    LINE 6:   IF n <> :oczekiwana THEN
```

Skutek byl **glosny i nieszkodliwy** - `ON_ERROR_STOP`, transakcja sie wycofala. Ale bramka
NIE DOSZLA DO WYKONANIA. Gdyby ten sam blad siedzial po drugiej stronie sztuczki (bramka niby
jest, tylko porownuje z wartoscia pusta), migracja przeszlaby BEZ kontroli i nikt by tego nie
zauwazyl.

**Regula: bramke trzeba ZOBACZYC przy pracy, zanim sie jej zaufa.** Po poprawce uruchomilismy
plik najpierw ze ZLA liczba i potwierdzilismy, ze sie zatrzymuje. Bramka, ktorej nikt nie widzial
w dzialaniu, jest zalozeniem, nie zabezpieczeniem - AP-311 zastosowane do wlasnego narzedzia.

## 4. Cztery korekty Tomasza, wszystkie weszly

1. Nazwa `handed_off` zamiast `awaiting_*` (punkt 1 wyzej).
2. Trzeci pisarz zweryfikowany: predykat `status='needs_approval'` sprawia, ze bot **nie musial
   byc gaszony** - nie potrafi ani utworzyc, ani skonsumowac migrowanej wartosci.
3. **Pulapka znacznika obrazu.** Stary obraz zamrozony jako `cm-agent:prev-d008`, nowy zbudowany
   jako `cm-agent:d008`, `latest` przestawiony dopiero po zielonym oknie. Gdyby nowy obraz
   powstal pod `latest`, komenda ratunkowa z masterpromptu podnioslaby NOWY kod na
   NIEZMIGROWANYCH danych - bez zadnego objawu, bo alarm zwisu iteruje po tej samej pustej liscie.
4. **Aktywacje potwierdza ZACHOWANIE**, nie odpowiedz 200 ani flaga `active`. Skrypt czekal na
   nowe wykonanie: `95161 (success) 19:42:00`.

## 5. Wada, ktora build wprowadzil sam - zlapana przed wdrozeniem

Zamiana literalu na `%s` zostawila trzecie uzycie wspolnego fragmentu `base_q`
(`conversation.py`) bez parametru, kilkadziesiat linii ponizej czytanego miejsca. Objaw bylby
u Tomasza, nie w zestawie: blad przy pierwszym zadaniu grafiki bez podanego tematu.

Zlapal to statyczny przeglad AST. Zostal jako staly test: `test_sql_parametry.py`, 432 policzalne
zapytania, zakres nazw **per funkcja** (jeden slownik na plik dawal falszywy alarm, bo
`conversation.py` ma dwie rozne zmienne `base_q`).

## 6. Co zostaje otwarte

**D-008b** (zapisany swiadomie): stara wartosc `dispatching` nadal stoi w ograniczeniu `CHECK`.
Dopoki tam jest, obraz `cm-agent:prev-d008` da sie podniesc - to jedyna droga odwrotu.
Osobne okno, z limitem czasu blokady: `docs/ops/SQL_d008b_sprzatanie_check_PO_OKNIE.sql`.
**Do jego zamkniecia nie kasowac obrazu `cm-agent:prev-d008`.**

**Czego to okno NIE udowodnilo:** sciezka `approved -> handed_off -> published` nie przebiegla
w produkcji, bo nic sie nie publikowalo. Dowodem bedzie pierwsza publikacja po zatwierdzeniu
materialu. **D-008 jest wdrozone, ale nieprzecwiczone** - i tak nalezy o nim mowic, dopoki
material nie przejdzie tej drogi sam.

---

**Zestaw testow: 25/25** (bylo 23/23; doszly `test_d008_handed_off.py` z 24 asercjami
i `test_sql_parametry.py`). Test D-008 sprawdzony **pieciema celowymi przywroceniami wady**,
w tym przywroceniem "nadgorliwym" - migracja slownika `post_queue`, ktorej robic NIE WOLNO.
