# ZGŁOSZENIE do Managera - 22.08.2026: CM ma być partnerem, nie tablicą wyników

**To jest najważniejsza rzecz, jaka padła dziś, i nie jest to prośba o funkcję.**
Tomasz nazwał wprost, dlaczego system, który działa, nadal nie zdejmuje z niego pracy.
Zgłaszam to jako wymaganie produktowe do Twojej decyzji, nie jako zadanie do wykonania.

## Dowód: odprawa poranna CM z 22.08, godz. 09:00

Bot przysłał dokładnie to:

> 🗓 Odprawa poranna CM:
> - 1 materialow czeka na przeglad (karty)
> - 43 pomyslow czeka na decyzje intake (Kolejka/Dzis/Odrzuc)
> - 20 pozycji planu czeka na akceptacje
> Co odblokowac najpierw? Moge tez cos przesunac albo dorzucic tematy - napisz.
>
> `[🔍 Przegladaj materialy (1)]`

**Cztery liczby, jeden guzik prowadzący do najmniejszej z nich.**

## Co Tomasz powiedział, jego słowami

> „wszystko jest w jednym chacie i gubię się w materiałach do publikacji"
>
> „jak przeglądać propozycje, jak planować kolejność? to chciałem by robił CONTENT MANAGER"
>
> „nie mam guzików typu przeglądaj propozycję, nie mam guzika zaproponuj kolejność publikacji
> na wszystkie dostępne kanały, nie mam omówienia strategii publikacji i ewentualnie naniesienia
> przeze mnie zmian"
>
> „Chcę z CM odprawiać się jak z partnerem i uważam, że musi mieć swój dedykowany telegram"

## Diagnoza z odczytu kodu, nie z domysłu

**1. Odprawa RAPORTUJE ZALEGŁOŚCI, zamiast PROPONOWAĆ DECYZJĘ.**
Pyta „co odblokować najpierw?", czyli oddaje Tomaszowi robotę planowania, którą CM miał wykonać
za niego. Partner przychodzi z propozycją i pyta o zgodę. Ta odprawa przychodzi z listą i pyta
o polecenie. To jest różnica między współpracownikiem a formularzem.

**2. 43 pomysły i 20 pozycji planu nie mają ŻADNEGO guzika.** Największe zaległości są jedynymi
bez drogi wejścia. Guzik prowadzi do jednego materiału. Żeby ruszyć czterdzieści trzy, trzeba
wiedzieć, jaką komendę wpisać - czyli pamiętać interfejs, którego nie widać.

**3. Nie ma widoku KOLEJNOŚCI ANI STRATEGII.** Jest przegląd karta po karcie (jeden materiał
naraz) i jest plan do akceptacji pozycja po pozycji. Nie ma miejsca, w którym Tomasz widzi
**co i w jakiej kolejności pójdzie na wszystkie kanały**, ani w którym może to przestawić.
Decyzje są atomowe, a myślenie o publikacji jest sekwencyjne - narzędzie nie pasuje do zadania.

**4. Jeden bot udaje wielu agentów.** `cm-agent/app/conversation.py:126`, komentarz w kodzie:
*„jeden bot udaje wielu agentow przelacznikiem /agents"*. Stan aktywnego agenta jest trzymany
per `chat_id` w `user_agent_state`. Skutek: Content, Sprzedaż i reszta dzielą jeden strumień
wiadomości. Materiały do publikacji przeplatają się z kartami sprzedażowymi i meldunkami
subagentów. **„Gubię się" nie jest wrażeniem, tylko przewidywalnym skutkiem tej architektury.**

## To NIE jest nowe odkrycie i to jest osobno ważne

`project_cm_real_scope` (pamięć trwała) mówi od dawna: zbudowany jest **kręgosłup wykonawczy,
około 10 procent**, a prawdziwy CM to **planer plus dwustronna rozmowa plus nadzór subagentów**.
`feedback_cm_dialogical_partner`: CM ma mieć własne zdanie i trafne pytanie, nie transakcyjne
„zrobione".

Wiedzieliśmy o tej luce i przez ten czas budowaliśmy niezawodność egzekucji: bramki, walidatory,
blokady. **To była właściwa kolejność** (dwa publiczne wycieki uzasadniają każdą z tych bramek),
ale skutek uboczny jest taki, że wzmacnialiśmy część, która i tak działała, a część, dla której
CM powstał, stoi w tym samym miejscu od miesięcy. Operator właśnie to nazwał.

## Pytania do rozstrzygnięcia

1. **Czy dedykowany Telegram dla CM wchodzi jako osobny blok, i kiedy?** Dwie drogi: wątki
   w grupie (Telegram Topics, jeden bot, tanio) albo osobny bot per dział (droższe, ale pełne
   rozdzielenie powiadomień i historii). Rekomendacja BE: **Topics**, bo nie mnoży tokenów
   ani wdrożeń, a rozdziela to, co boli - strumień i powiadomienia.
2. **Czy odprawa poranna ma proponować kolejność, zamiast pytać, co odblokować?** To zmiana
   kontraktu odprawy, nie kosmetyka: CM ma przyjść z planem dnia i prosić o weto, tak jak
   D-D z 14.08 zmienił zgodę na publikację w prawo weta.
3. **Czy przegląd kolejności na wszystkie kanały to osobny widok?** Dziś nie ma niczego takiego.
4. **Priorytet wobec kolejki technicznej.** Zostały: faza 3 okna (D-017), blok H (D-024),
   D-023, D-025, D-026. Ta sprawa jest produktowa i moim zdaniem **ważniejsza dla Tomasza niż
   którakolwiek z nich**, ale nie przestawiam kolejności bez Twojej decyzji.

## Kontekst, który ma znaczenie przy tej decyzji

Tomasz powiedział wprost: **„kończmy ten system niech on pracuje za mnie, bo już czasu nie mam"**.
To jest kryterium odbioru dla CM i warto je zapisać jako takie: system, który raportuje zaległości,
nie pracuje za operatora, tylko dokłada mu decyzji.
