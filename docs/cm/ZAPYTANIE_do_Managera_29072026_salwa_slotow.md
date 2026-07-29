# ZAPYTANIE do Managera AGS: salwa slotów, cztery decyzje (29/07/2026)

Od: AGS Build Engineer. Poprzedzające: raport diagnostyczny z tego samego dnia (rozsypanie
serii na X) oraz ustalenie o pochodzeniu slotu 09:00.

Zero zmian w kodzie. Wszystko poniżej to odczyt i decyzje, o które proszę.

---

## 1. Co ustalone (skrót, szczegóły były w raporcie)

**Mechanizm salwy: `conversation.py:1286-1290`, trasa ręcznego przesunięcia terminu materiału.**
Jedna wartość podana przez człowieka ląduje w materiale i w **każdym** jego wierszu kolejki
naraz, dosłownie, bez rozsuwania części. Wszystkie inne drogi zapisu slotu wykluczone
z podaniem powodu.

**Kontrola okna istnieje i celowo nie blokuje** - dopisuje uwagę „ustawiam mimo to, bo Ty
decydujesz o terminie". Uważam tę decyzję za słuszną i nie proponuję jej zmiany.

**Wada leży w założeniu, nie w regule:** trasa zakłada, że jeden materiał to jeden wiersz
kolejki. Było prawdziwe, zanim powstały serie. Przy materiale pięcioczęściowym jedno
przesunięcie zbija pięć wpisów na jedną minutę - salwa, o której nikt nie decydował, bo
człowiek podał jeden termin, a nie pięć.

**Skala:** 81 z 264 wierszy X ma slot identyczny ze slotem materiału. Salwa powstaje tylko
tam, gdzie materiał ma wiele wierszy, stąd pięć przypadków w czternaście dni.

**To nie jest regresja po zmianach z 25-27/07.** Trasa jest starsza, salwy z 18 lipca to
potwierdzają.

---

## 2. Pytanie pierwsze, najpilniejsze: co z seriami, które JUŻ są w kolejce

Twoja decyzja „X dostaje jeden wpis na materiał" dotyczy tego, co CM dopiero wyprodukuje.
Ale w kolejce siedzą już materiały pocięte na serie i **one wyjdą same**, bez niczyjej decyzji:

| materiał | części czekających | pierwszy slot |
|---|---|---|
| Cost-aware AI w praktyce | 10 | 31/07 21:01 |
| Orkiestracja: agent deleguje do agenta | 5 | 29/07 16:30 |
| Debugowanie systemu agentów | 5 | 30/07 18:47 |
| Automatyzacja która shipuje | 4 | 03/08 16:33 |
| Próg pewności klasyfikatora | 4 | 06/08 17:55 |

To jest dwadzieścia osiem wpisów rozłożonych na dziesięć dni, w formie, którą właśnie
zdecydowałeś wycofać. Do tego **dopóki one tam są, jedno „przesuń" nadal potrafi zrobić
salwę** - to jest jedyne żywe ryzyko z całej tej sprawy.

**Trzy drogi, rekomendacja BE pierwsza:**

1. **Zostawiamy, niech wyjdą.** Są zatwierdzone, czytelne jako samodzielne wpisy (prompt
   tego wymagał), a wstrzymanie ich zostawia dziesięciodniową dziurę w kadencji na koncie,
   które i tak ma martwy zasięg. Nowa forma wchodzi od następnej produkcji CM.
   **Ryzyko do przyjęcia świadomie:** przez dziesięć dni jedno nieuważne przesunięcie
   materiału może wystrzelić do dziesięciu wpisów naraz.
2. **Wstrzymujemy części od drugiej wzwyż**, zostawiając z każdego materiału pierwszą.
   Kadencja rzednie, ale forma jest od razu zgodna z decyzją i ryzyko salwy znika dziś.
3. **Scalamy części z powrotem w jeden wpis.** Najczystsze wobec decyzji, ale to przepisanie
   treści, czyli robota CM i Twoja akceptacja, nie moja poprawka.

## 3. Pytanie drugie: czy trasa przesunięcia ma rozsuwać części

Niezależnie od tego, co zrobimy z zastaną kolejką, sama trasa zostaje.

**Rekomendacja BE: rozsuwać.** Pierwsza część na termin podany przez człowieka, kolejne na
następne wolne sloty kanału. Zachowuje intencję („ten materiał ma iść od dziewiątej") i nie
tworzy salwy, o której nikt nie decydował.

Alternatywa: blokować przesunięcie materiału wieloczęściowego i kazać przesuwać wiersze
pojedynczo (`_sub_reschedule` już to umie, celuje w jeden wiersz). Uczciwsze wobec człowieka,
ale uciążliwe przy dziesięciu częściach.

Trzecia droga: nie ruszać niczego, bo po Twojej decyzji serie i tak przestaną powstawać.
Broni się, jeśli wybierzesz drogę 2 albo 3 z pytania pierwszego.

## 4. Pytanie trzecie: ostrzeżenie o oknie przy wielu wierszach

Dziś ostrzeżenie o publikacji poza oknem to jedno zdanie w odpowiedzi. Przy jednym wpisie
w zupełności wystarcza.

**Rekomendacja BE:** przy materiale mającym więcej niż jeden wiersz i terminie poza oknem
zamienić notatkę na **pytanie z guzikami**. Powód nie jest formalny: 25 lipca konto dostało
403 za wykrytą automatyzację, a trzy dni później wyszło pięć wpisów w pięć minut o dziewiątej
rano. Notatka w odpowiedzi tego nie zatrzymała, bo nie miała czego zatrzymać - nikt nie wiedział,
że jedno polecenie dotyczy pięciu wpisów.

## 5. Pytanie czwarte: ślad audytowy slotu

Ani `post_queue`, ani `content_items` nie zapisują, **kto** i **kiedy** ustawił slot.
Pochodzenie tych pięciu wpisów ustaliłem eliminacją wszystkich innych dróg zapisu, a nie
śladem w danych. Przy następnym takim pytaniu zajmie to tyle samo czasu.

**Rekomendacja BE: tak, ale mały.** Jedna kolumna z etykietą źródła (`planner`, `staging`,
`reslot`, `rozmowa`, `n8n`) wpisywana przy każdym zapisie slotu. Bez nazwisk i bez historii,
sama etykieta. To jest ta sama klasa co AP-311: brak danych nie jest faktem o świecie, dopóki
nie sprawdzisz, czy system miał jak je pokazać - tu po prostu nie miał.

---

## 6. Nadal otwarte z wcześniejszych ustaleń

- **Pole formatu (wpis / Article)** - czeka na moment, w którym CM zacznie produkować
  jednoczęściowo. Zgodnie z Twoim poleceniem nie ruszam tego po swojej stronie.
- **D-006, widok stanu `dispatching`** - zapisane jako dług, nie naprawiane.
- **Bio profilu i compliance treści statycznych** - potwierdzone, że nic nie czyta własnych
  profili, więc nie ma czego egzekwować. Osobna decyzja, czy budujemy taki organ.
- **Brak walidacji długości przed wysyłką na X** - potwierdzony. Dwa progi w kodzie, jeden
  uruchamia cięcie zamiast odrzucenia, drugi jest martwy (sprawdza znacznik `===TWEET===`,
  gdy reszta systemu używa `===POST===`). Po Twojej decyzji o jednym wpisie ta walidacja
  staje się potrzebna, bo nie będzie już cięcia, które maskowało brak limitu.
