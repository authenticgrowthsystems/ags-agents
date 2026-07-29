# PRZEKAZANIE do Content Managera: 21 materiałów do przerobienia na jeden wpis (29/07/2026)

Od: AGS Build Engineer, na polecenie Managera AGS.

## Co się stało

**Decyzja produktowa Managera 29/07: X dostaje jeden wpis na materiał. Koniec serii
wieloczęściowych.** Jeśli myśl nie mieści się w jednym wpisie, ma dwie drogi: albo idzie jako
X Article, albo nie idzie na X w ogóle i zostaje na LinkedIn.

**Dziś wycofałem z kolejki 21 materiałów (99 wierszy).** Wszystkie były seriami po 3-10 części.
Powód nie był estetyczny: 28/07 pięć części jednego materiału wyszło na X w pięć minut, o 09:00,
poza oknem publikacji, na koncie które trzy dni wcześniej dostało 403 za wykrytą automatyzację.
Dopóki serie stały w kolejce, jedno przesunięcie terminu mogło powtórzyć to na dziesięciu wpisach.

**Po operacji w kolejce X nie ma nic - zero wierszy oczekujących.** Kadencja X stoi, dopóki
nie wyprodukujesz w nowej formie.

## Jak rozpoznać te materiały samodzielnie

```sql
SELECT p.content_item_id, left(ci.master_theme, 80) AS temat, COUNT(*) AS czesci
FROM post_queue p JOIN content_items ci ON ci.id = p.content_item_id
WHERE p.platform = 'x' AND p.status = 'rejected'
  AND p.updated_at::date = DATE '2026-07-29'          -- BEZ tego warunku wyjdzie 26, nie 21
GROUP BY 1, 2 HAVING COUNT(*) > 1
ORDER BY czesci DESC;
```

**Warunek daty jest konieczny.** Bez niego zapytanie zwraca 26 materiałów - pięć z nich zostało
odrzuconych wcześniej, przy zwykłym przeglądzie kart, i nie mają nic wspólnego z tą operacją.
W bazie nie ma dziś znacznika, który by je rozróżniał. To jest znany brak, zapisany jako D-007.

**Treści części są zachowane** w `post_queue.content` - żeby wyciągnąć materiał do przepisania:

```sql
SELECT id, left(content, 200), scheduled_for
FROM post_queue WHERE content_item_id = '<id z listy>' ORDER BY id;
```

## Lista: 21 materiałów, wszystkie wycofane 29/07

| części | identyfikator materiału | temat |
|---|---|---|
| 10 | c1a5cf81-b94f-4b9c-9fb6-566ab45e17d5 | Cost-aware AI w praktyce: jak liczyc koszt konwersacji end-to-end |
| 6 | 287a812c-cf07-4f2d-9b6e-454d519fef5d | Warstwa weryfikacji przed odpowiedzia do klienta |
| 5 | 00de7b3e-a74d-47cf-b222-cce1f8c97dbf | AI agents dla realnego biznesu: jak odroznic problem ktory faktycznie... |
| 5 | 9861ae00-bc47-4d30-b5d9-d8a05e394426 | Blad 422 ktory nic nie znaczy dla klienta: rozdzielenie odpowiedzi |
| 5 | ef76c083-d483-476c-a577-311c0025660b | Debugowanie systemu agentow: dlaczego wiekszosc awarii jest cicha |
| 5 | 6692ac05-828e-4ad0-bcdf-9a0f8d729327 | Dwie warstwy obserwowalnosci klienta |
| 5 | 849a9523-5f4c-47fa-a9bc-dfe4250d7b5e | Idempotentnosc platnosci jako fundament architektury agentowej |
| 5 | e7c94ced-8622-438a-b1e7-75362d4555d2 | Latencja jednego agenta vs czterech w chainie |
| 5 | 5e6928f5-81e8-4da0-8654-69f9168c0d18 | Odpowiedz w 5 minut nawet w niedziele o 22 |
| 5 | bf292567-fe4c-4929-a2d8-361bfed06703 | Specjalizacja agentow ma sens tylko gdy zadania maja rozna nature |
| 5 | 5ef27d68-695c-49b1-a1c2-11388bd7ec17 | Werdykt agenta jako granica odpowiedzialnosci wobec czlowieka |
| 4 | be5b395c-2ade-4875-a928-4acb5ce7b742 | Agent gotowy do zamkniecia kontraktu 8K: dlaczego ostatni krok |
| 4 | cd36a33f-4b65-46da-a355-31e982a7a7fd | Automatyzacja ktora shipuje: minimalny agent |
| 4 | 6cd75aa1-ec71-40e5-a630-f8f05d6bea9f | Cost-aware AI jako dyscyplina projektowa |
| 4 | ca8c9898-8f62-45aa-8566-7fe56ba9f756 | Diagnoza gdzie wycieka 40% pieniedzy |
| 4 | 69927261-1003-4833-83bc-7a936df7f29c | Granice pojedynczego agenta: sygnaly ze rozrasta sie w monolit |
| 4 | f303514b-535e-4c95-b52b-ef804f7ffbdc | Orkiestracja: agent deleguje do agenta |
| 4 | f4e69eeb-6bab-483c-b21b-ad212ddd100b | Prog pewnosci klasyfikatora: co robi agent gdy nie jest pewny |
| 4 | 7eaa2e2d-96e3-4242-8eef-bf0b0f55f2e4 | Retencja jako sekwencja konkretnych dzialan |
| 3 | dc40b2a5-55f2-49d2-a24d-11f03334c7a6 | Lead z formularza ktory czeka 4 godziny na odpowiedz |
| 3 | 84ce5e16-55b7-4b9e-9766-b5a3c60e2e9f | Retry bez idempotencji to nie odpornosc |

**Jeden z nich wyszedł częściowo:** "Orkiestracja" zdążyła opublikować pierwszą część 29/07
o 16:30, zanim wycofałem resztę. Przy przepisywaniu weź to pod uwagę.

## Czego NIE zmieniaj po swojej stronie bez sygnału

Prompt generujący nadal każe rozkładać długą treść na 3-5 samodzielnych wpisów
(`generate.py`), a staging nadal tnie po separatorze `===POST===`. **Manager wprost polecił,
żeby BE tego nie ruszał, dopóki Ty nie zaczniesz produkować jednoczęściowo** - inaczej
rozjedziemy się w połowie drogi. Kolejność jest taka: najpierw Twoja nowa forma, potem BE
zdejmuje cięcie i dokłada pole formatu oraz walidację długości.

Do tego czasu: jeden materiał = jeden wpis, pisany tak, żeby bronił się sam.
