# Kanon zimnej wysyłki (decyzje Managera 27/07/2026)

Krótki dokument, bo decyzje są krótkie. Powstał, gdy kampania weszła w fazę ręcznej,
spersonalizowanej wysyłki do zaimportowanej listy szkół tańca.

---

## 0. POZYCJONOWANIE: przedsionek, nie zamiennik (korekta Managera 27/07 wieczorem)

**To jest najważniejsza część tego dokumentu.** Research trzech źródeł dał sprzeczne werdykty
i sprzeczność rozstrzyga się tak:

**Nasze narzędzie jest przedsionkiem, nie zamiennikiem systemu do zapisów.** Większość polskich
szkół tańca trzyma bazę kursantów w **ActiveNow** i nikt jej nie migruje.

Obsługujemy wszystko, co dzieje się **zanim** ktoś stanie się kursantem: nieodebrany telefon,
wiadomość w niedzielę wieczorem, formularz z Facebooka, pytanie o pierwszy taniec. Dopiero
zapisany człowiek wchodzi do ActiveNow i tam zostaje.

**ZAKAZ ABSOLUTNY: nie proponujemy migracji bazy ani rezygnacji z obecnego systemu zapisów.**
To jest największy strach właściciela szkoły i jednocześnie rzecz, której nie musimy ruszać.
Jedno zdanie o "przeniesieniu bazy" potrafi zabić rozmowę, której nic innego by nie zabiło.

**Synchronizacja przez API to etap drugi** - nie sprzedajemy jej na wejściu.

## 0.1 Trzy argumenty, w tej kolejności ważności

1. **Trzy subkonta w cenie jednej subskrypcji.** Szkoła ma zwykle trzy linie: kursy regularne,
   pierwszy taniec, imprezy. Dziś wszystkie wpadają do jednej skrzynki. Dowód własny: Tomasz
   nie puszcza pierwszego tańca przez stronę Royal Dance, tylko przez dedykowaną.
2. **Rachunek spina się przed retencją.** Tomasz zszedł z 2500 zł rocznie za hosting na 200 zł,
   bo strony stoją w narzędziu. Do tego odpada Calendly i osobny mailing. Dla szkoły płacącej
   dziś agencji za hosting narzędzie zwraca się **z samych rachunków**, zanim zatrzyma pierwszego
   kursanta. To argument z faktury, nie z obietnicy, więc idzie w rozmowie **przed** retencją.
3. **Wdrożenie nie jest dodatkiem do subskrypcji, tylko warunkiem jej sensu.** Research podaje
   3-4 tygodnie codziennego używania do swobody w panelu i 2-3 miesiące do stabilnego systemu.
   Właściciel szkoły tego czasu nie ma. **Sprzedajemy zdjęcie trzech tygodni, nie dostęp
   do narzędzia.**

## 0.2 Konkrety wdrożeniowe

- **Komunikacja masowa w Polsce idzie przez WhatsApp, nie SMS-em.** SMS do Polski to około
  17 gr za segment, WhatsApp użytkowy około 5 gr plus 10 USD miesięcznie za subkonto.
  **SMS zostaje wyłącznie przy nieodebranym połączeniu**, gdzie liczy się dotarcie, a wolumen
  jest mały.
- **RODO mówimy wprost:** serwery w Stanach, zgodność przez umowę powierzenia i ramy EU-US.
  Dla szkoły tańca wystarcza.
- **Branże zdrowotne: piszemy do nich normalnie** (decyzja Tomasza 27/07, **cofa wykluczenie
  Managera z tego samego dnia**). Uzasadnienie właściciela: *"nie wycinamy rodziny zdrowie
  i uroda wcale, będziemy próbować i zobaczymy, mail i SMS nic nie kosztuje jak wyślę ręcznie"*.

  **Rozdzielenie, które warto trzymać:** zastrzeżenie Managera dotyczyło WDROŻENIA, nie wysyłki.
  Próba kontaktu nie niesie żadnego ryzyka; problem RODO powstaje dopiero, gdy dane pacjentów
  miałyby usiąść na serwerach w Stanach.

  **Korekta pozycjonowania w dużej mierze to rozbraja.** Skoro sprzedajemy przedsionek i nie
  ruszamy systemu, w którym siedzi kartoteka, to u fizjoterapeuty tak samo nie ruszamy jego
  systemu pacjentów, jak u szkoły tańca nie ruszamy ActiveNow. "Macie wolny termin we wtorek"
  nie jest daną o zdrowiu.

  **Czego nie wolno przemilczeć przy wdrożeniu:** wiadomość przychodząca potrafi sama nieść
  informację o zdrowiu ("boli mnie kręgosłup, macie termin"), a tego nie da się z góry
  powstrzymać. Mówimy o tym wprost i ustalamy zakres, zamiast udawać, że problemu nie ma.

## 1. Z jakiego adresu piszemy

**`tomasznawrocki.pl`** - do zimnej wysyłki do szkół tańca.

Nic nie kupujemy, Tomasz ma jedenaście własnych, skonfigurowanych domen. Wybór nie jest
techniczny, tylko pozycyjny:

- **`royaldance.pl` i `royaldancecenter.pl` odpadają.** Pisząc z nich do szkoły tańca,
  jesteś dla odbiorcy konkurencyjną szkołą tańca z Opola. Żadna warstwa techniczna,
  żaden ton i żadna personalizacja tego nie odrobi.
- **`authenticgrowthsystems.com` odpada.** To jedyny adres, na który odpisze płacący
  klient - nie palimy go zimną wysyłką.

## 2. Ile płacimy za personalizację

**Natywne źródło `site` domyślnie dla wszystkich, płatny research dla maksimum dziesięciu.**

- `site` czyta stronę podmiotu natywnie, bez kosztu API, i daje hak z faktami z tej strony.
  To jest domyślne paliwo personalizacji.
- Płatny research (tier medium, około 1-2 PLN) **tylko tam, gdzie Tomasz zna kogoś osobiście
  albo podmiot jest wyraźnie większy od reszty**. Maksimum dziesięć sztuk, czyli około
  dwadzieścia złotych zamiast dwustu dwudziestu.

Uzasadnienie Managera jest ekonomiczne, nie oszczędnościowe: przy szkole tańca oferta to
97 USD miesięcznie plus wdrożenie. Dwa złote researchu na sztukę bronią się przy JEDNYM
prospekcie, nie przy stu dziesięciu wysłanych w ciemno. **Przy Adamietzu płatny research
jest oczywisty i tam się go nie żałuje.**

## 3. Kolejność budowy (STOP cofnięty 27/07 wieczorem)

**Decyzja Tomasza, przekazana przez Managera: budowa idzie RÓWNOLEGLE z pozyskiwaniem.**
Jedno nie blokuje drugiego - BE buduje, Tomasz w tym samym czasie dzwoni i pisze ręcznie.

Wcześniejsza tego samego dnia decyzja o zatrzymaniu łańcucha po wzbogacaniu **już nie
obowiązuje**. Powód cofnięcia: zatrzymanie zakładało, że budowa konkuruje z pozyskiwaniem
o czas Tomasza. Nie konkuruje - to dwie różne pary rąk.

**Kolejność po zamianie (rekomendacja BE przyjęta przez Managera):**

1. ~~Import listy z kwalifikacją~~ - **zrobione 27/07**.
2. **Zbieracz podmiotów z rejestrów po PKD** - następny. CEIDG i KRS/REGON mają oficjalne API,
   dane jawne, filtr po PKD i województwie daje powtarzalny wolumen w każdej niszy.
3. **Wysyłka automatyczna** - na koniec, i to świadomie. Ręczna wysyłka nie jest wąskim
   gardłem (Tomasz woli pisać sam, bo ręcznie znaczy personalnie), a automat tworzyłby ryzyko
   domeny i tonu, którego dziś nie mamy.

Scraping Map Google nadal odpada: łamie regulamin, a Places zabrania trwałego składowania
wyników. Mapy do uzupełnienia pojedynczego rekordu, nie do budowy bazy.

## 4. Zakres pilotażu

**Jedna nisza: taniec.** Cztery rodziny nisz zostały omówione i odrzucone jako równoległe -
jedna pilotażowa idzie do końca łańcucha, reszta czeka.

---

Powiązane: `docs/komponenty/maszynka-prospektowa.md` (ogniwo 1 i wzbogacanie),
`docs/product/OFERTA_DFY_RETENCJA.md` (co sprzedajemy), `anti-patterns/library.md` AP-311.
