# RUNBOOK DFY: System Retencji Klientow - wdrozenie u klienta krok po kroku

Status: v1 (20/07/2026, BE-PRODUKT). Dokument WEWNETRZNY dla Tomasza (test krzeslem: da sie
wykonac czytajac po kolei, bez zgadywania). Narzedzie wewnetrznie = GoHighLevel (GHL);
w komunikacji z klientem NIGDY nie ujawniamy nazwy. Szablony wiadomosci do wklejenia klientowi
maja pelne polskie znaki; reszta dokumentu = ASCII repo.
Zrodla: pricing_tiers lokalna_automatyzacja (zakres pakietow), vendor_registry (GHL config,
lekcje DNS/Mailgun), sales_sequences (kadencja 48h/5d/8d), sales_playbook (Sales Bible v0.2),
know-how RDC/TNM (GHL w produkcji od 2026).

Czas calkowity wg pakietu: Fundament 5-7 dni / Pakiet 2 7-10 dni / Pakiet 3 10-14 dni.
Czas PRACY Tomasza: ok. 6-10h (P1) / 12-18h (P2) / 20-30h (P3) - reszta to czekanie na
materialy klienta i propagacje DNS.

---

## KROK 0. PRZED PIERWSZA ROZMOWA (15 min)

Checklist przygotowania:
- [ ] Obejrzyj strone / profil firmy klienta (Google, FB, IG). Zanotuj: co sprzedaje, jak
      pozyskuje klientow, czy ma rezerwacje online, ile ma opinii w Google i kiedy ostatnia.
- [ ] Wyslij klientowi 1 zdanie: "Przygotuje sie do rozmowy - prosze o adres strony www
      i nazwe firmy w Google, nic wiecej na razie nie potrzebuje."
- [ ] Przygotuj kartke/notatke z sekcja discovery (nizej) - NIE improwizuj listy pytan.

## KROK 1. DISCOVERY 30 MIN (rozmowa, nie prezentacja)

Regula: Ty pytasz, klient mowi. Zero pokazywania narzedzia. Cel = mapa wyciekow + dane do
konfiguracji. Notuj DOSLOWNIE (jego slowa wracaja potem w tresciach wiadomosci).

Pytania (kolejnosc celowa, wartosc przed mechanizmem):
1. "Skad dzis przychodza klienci?" (kanaly: telefon / FB / polecenia / wejscie z ulicy)
2. "Co sie dzieje, gdy ktos napisze albo zadzwoni, a Pan/Pani nie moze odebrac?" (WYCIEK #1)
3. "Ilu klientow wraca drugi raz? Skad Pan/Pani to wie?" (WYCIEK #2 + czy ma jakakolwiek baze)
4. "Jak wyglada umawianie wizyt/terminow? Kto pilnuje przypomnien?" (WYCIEK #3)
5. "Kiedy ostatnio poprosil Pan/Pani klienta o opinie w Google?" (WYCIEK #4)
6. "Gdzie jest dzis lista klientow? (zeszyt / telefon / Excel / nigdzie)" (dane do importu)
7. "Gdyby jedna rzecz miala sie naprawic sama, co by to bylo?" (priorytet wdrozenia = jego
   slowa, uzyj ich w szkoleniu i raporcie)

Wyjscie z discovery (bez tego NIE zaczynaj setupu):
- [ ] branza + 1-3 uslugi glowne z cenami
- [ ] wyciek nr 1 wg klienta (jego slowami)
- [ ] zrodlo bazy klientow (plik / eksport / brak)
- [ ] dostepy: domena (gdzie kupiona, login), wizytowka Google, logo, kolory, zdjecia
- [ ] decyzja pakietu (top-down: zaproponuj pelny zakres, schodz TYLKO na jawny sygnal)
- [ ] platnosc setupu ustalona (FV + przelew; 50% zaliczki przed startem)

## KROK 2. KONTO NARZEDZIA (klient placi sam) - 30 min + czekanie

1. Klient zaklada WLASNE konto GHL (Starter $97/mc; Unlimited $297/mc gdy Pakiet 3 z wieloma
   uzytkownikami/markami). Docelowo przez link partnerski AGS (40% prowizji cyklicznej) -
   jesli link jeszcze nie istnieje, klient rejestruje sie wprost, NIE blokuj wdrozenia.
2. Wyslij klientowi instrukcje (szablon A ponizej): rejestracja + dodanie Ciebie jako
   uzytkownika (rola admin) na czas wdrozenia.
3. Zapisz w naszej bazie: contacts (relationship_stage='client') + notatka location_id
   klienta. NIE mieszaj z naszym multi-tenant sub-accountem RDC (FAxCpFiV8RrnzLTtpAZQ) -
   klient MA WLASNE konto, to jest fundament modelu (wlasnosc danych po jego stronie).

LEKCJE Z PRODUKCJI (vendor_registry, nie powtarzaj bledow):
- E-mail wysylkowy (subdomena lc.domena-klienta.pl): 6 rekordow DNS per domena wysylkowa;
  rekordy MX MUSZA byc FQDN z kropka na koncu ("lc.domena.pl."), TXT/CNAME moga byc relative.
- Konfiguracja domeny e-mail w GHL jest per SUB-ACCOUNT (nie per workflow) - u klienta
  z wlasnym kontem to bez znaczenia, ale przy multi-brand pamietaj (support Meera A. 15/05).
- Propagacja DNS trwa do 24-48h - odpal ja PIERWSZEGO dnia wdrozenia, resztę rob w miedzyczasie.
- SMS w PL: przez LC Phone/Twilio w GHL; ceny za SMS ponosi klient (z jego abonamentu/salda).
  Powiedz to wprost przy szkoleniu (zero niespodzianek na fakturze).

## KROK 3. FUNDAMENT KONTA (dzien 1-2)

- [ ] Business Profile: nazwa, adres, NIP, godziny pracy, strefa Europe/Warsaw, jezyk PL.
- [ ] Domena: podpiecie strony (Pakiet 1-3) + subdomena wysylkowa e-mail (patrz lekcje wyzej).
- [ ] Telefon: numer do powiadomien wlasciciela; opcjonalnie numer SMS (koszt po stronie klienta).
- [ ] Kalendarz: uslugi glowne jako typy wizyt (nazwy DOKLADNIE jak u klienta, AP-003:
      zero wymyslania nazw uslug), bufory, godziny.
- [ ] Import bazy: CSV z discovery (imie, telefon, e-mail, ostatnia wizyta jesli jest).
      Przy imporcie tag "import-YYYYMMDD" (latwy rollback). RODO: patrz KROK 7.
- [ ] Uzytkownicy: klient (owner) + Tomasz (admin, do zdjecia po przekazaniu jesli klient
      nie bierze opieki).

## KROK 4. PIPELINE / SCIEZKA KLIENTA (dzien 2)

Jeden pipeline "Klienci" - etapy uniwersalne (dostosuj nazwy do branzy klienta):
1. Nowe zapytanie  2. Skontaktowano  3. Umowiony termin  4. Usluga wykonana
5. Poproszony o opinie  6. Stały klient  7. Do odzyskania (90 dni ciszy)

Automaty przejsc: formularz/rozmowa -> etap 1; rezerwacja -> etap 3; wizyta odbyta -> etap 4
(wyzwala prosbe o opinie); brak aktywnosci 90 dni -> etap 7 (wyzwala sekwencje odzysku).

## KROK 5. SEKWENCJE (dzien 2-4) - SERCE PRODUKTU

Zasada tresci: kazda wiadomosc brzmi jak czlowiek, nie system (mom test, zero zargonu,
zero dlugich myslnikow, personalizacja imieniem i usluga). Ponizej 3 komplety per branza - wybierz jeden
i DOPASUJ slowami klienta z discovery. Wszystkie szablony: pelne polskie znaki, do wklejenia.

### 5a. USLUGI LOKALNE (warsztat, hydraulik, kosmetyka, serwis)

S1 Natychmiastowa odpowiedz na zapytanie (0 min, SMS + e-mail):
> "Dzień dobry! Tu {firma}. Dostaliśmy Pana/Pani wiadomość - oddzwonimy najpóźniej do
> {godzina}. Jeśli sprawa jest pilna, proszę napisać PILNE."

S2 Nieodebrane polaczenie (0 min, SMS):
> "Dzień dobry, tu {firma}. Widzę nieodebrane połączenie - już oddzwaniam, gdy tylko skończę
> z klientem. Można też od razu napisać, w czym pomóc."

S3 Przypomnienie o wizycie (24h przed + 2h przed, SMS):
> "Przypominamy: jutro {data} o {godzina} - {usługa} w {firma}, {adres}. Jeśli termin nie
> pasuje, proszę odpisać ZMIANA."

S4 Prosba o opinie (4h po wykonaniu uslugi, SMS):
> "Dziękujemy za wizytę w {firma}! Jeśli jest Pan/Pani zadowolona, będzie nam bardzo miło
> za krótką opinię w Google: {link}. To dla nas naprawdę dużo znaczy."

S5 Odzysk po 90 dniach ciszy (e-mail lub SMS):
> "Dzień dobry! Minęło trochę czasu od Pana/Pani ostatniej wizyty w {firma}. {sezonowy
> powód, np. przed zimą warto sprawdzić...}. W tym tygodniu mamy wolne terminy - odpisać
> z propozycją?"

### 5b. STUDIO / SZKOLA (tanca, jezykowa, fitness) - know-how RDC

S1 Zapis na zajecia probne (0 min, e-mail + SMS):
> "Cześć {imię}! Świetnie, że chcesz spróbować {zajęcia}. Twój termin: {data, godzina},
> {adres}. Weź wygodne buty i dobry humor. Do zobaczenia!"
(UWAGA: zajecia probne = "niezobowiązujące", NIGDY "bezpłatne" - AP-008.)

S2 Przypomnienie przed zajeciami (24h przed, SMS):
> "Do zobaczenia jutro o {godzina} na {zajęcia}! Jeśli coś Ci wypadło, daj znać - podamy
> inny termin."

S3 Po pierwszych zajeciach (nastepnego dnia, SMS):
> "Cześć {imię}, jak wrażenia po pierwszych zajęciach? Jeśli chcesz kontynuować, w tym
> tygodniu zapisy na {grupa/karnet}. Odpisz TAK, a zarezerwuję Ci miejsce."

S4 Koniec karnetu (7 dni przed koncem):
> "Hej {imię}, Twój karnet kończy się {data}. Przedłużyć na kolejny miesiąc, żeby nie
> stracić miejsca w grupie?"

S5 Odzysk nieobecnych (14 dni bez wejscia):
> "Cześć {imię}, nie było Cię ostatnio na {zajęcia} - wszystko w porządku? Grupa idzie
> dalej, ale spokojnie nadrobisz. Wracasz w {dzień}?"

### 5c. FREELANCER / USLUGI B2B (projektant, ksiegowa, fotograf)

S1 Autoodpowiedz na zapytanie ofertowe (0 min, e-mail):
> "Dzień dobry! Dziękuję za wiadomość. Przeczytam ją uważnie i wrócę z odpowiedzią do
> {dzień roboczy}. Jeśli sprawa jest pilna: {telefon}. Pozdrawiam, {imię}"

S2 Po wyslaniu oferty - kadencja 48h / 5 dni / 8 dni (z naszej sekwencji ABM; kazdy kontakt
DODAJE wartosc, nie "przypominam sie"):
- +48h: "Dzień dobry, podsyłam jeszcze {konkret: przykład realizacji / odpowiedź na pytanie
  z rozmowy}. Gdyby coś było niejasne w ofercie - jestem pod telefonem."
- +5 dni: "Dzień dobry, {jedna nowa informacja, np. wolny termin realizacji w {miesiąc}}.
  Czy temat jest jeszcze aktualny?"
- +8 dni: "Dzień dobry, zamykam u siebie kalendarz na {miesiąc}. Jeśli temat wróci później -
  proszę śmiało wracać, drzwi otwarte." (po tym: archiwum, zero dalszego nekania)

S3 Po zakonczonym projekcie (3 dni po oddaniu):
> "Dzień dobry, mam nadzieję, że {projekt} dobrze służy. Dwie prośby: krótka opinia w Google
> ({link}) i - jeśli zna Pan/Pani kogoś, komu przyda się {usługa} - będę wdzięczny za
> przekazanie kontaktu."

S4 Kontakt cykliczny (co kwartal, e-mail):
> "Dzień dobry, odzywam się jak co kwartał: {jedna konkretna rzecz, np. zmiana przepisów,
> nowa usługa, pomysł pod biznes klienta}. Bez zobowiązań - gdyby coś było potrzebne, jestem."

### Konfiguracja techniczna sekwencji (GHL)

- Kazda sekwencja = workflow z triggerem (formularz / status wizyty / tag / brak aktywnosci).
- Godziny wysylki: 9:00-19:00 Europe/Warsaw, nigdy w nocy; SMS bez niedziel (e-mail moze).
- Kazdy SMS konczy sie mozliwoscia rezygnacji zgodnie z ustawieniami narzedzia (STOP).
- Odpowiedz klienta ZATRZYMUJE sekwencje (warunek w workflow: reply -> stop) - czlowiek
  przejmuje rozmowe. To jest bezpiecznik przed "spamowaniem" (patrz FAQ objekcja 7).

## KROK 6. BRANDING (dzien 4-5, rownolegle)

- [ ] Logo, kolory, czcionki klienta w ustawieniach konta + szablonach e-mail.
- [ ] Stopka e-mail: dane firmy, telefon, adres, link do opinii Google.
- [ ] Strona (Pakiet 1-3): teksty z materialow klienta, jezyk korzysci ("co z tego mam"),
      formularz max 3 pola (imie, telefon, wiadomosc) - kazde dodatkowe pole obniza konwersje.
- [ ] Link do opinii Google: wygeneruj krotki link z wizytowki Google klienta i wstaw do S4.

## KROK 7. RODO / ZGODY (obowiazkowe w PL, 30 min)

- Import bazy: klient potwierdza (mailem, jedno zdanie), ze kontakty pochodza od jego
  klientow i ma prawo sie z nimi kontaktowac. My = podmiot przetwarzajacy na jego zlecenie.
- Formularz na stronie: checkbox zgody marketingowej (osobny od kontaktu w sprawie zapytania).
- Kazda wysylka masowa (kampanie, odzysk): tylko do kontaktow ze zgoda; SMS ze STOP.
- W umowie zlecenia: standardowe powierzenie przetwarzania (wzorzec umowy = osobny task,
  dziura #4 z TOP5 raportu stanu - do czasu wzorca: zapis o powierzeniu w mailu zleceniowym).

## KROK 8. TESTY (dzien 5-6; Pakiet 3: dzien 8-10) - test krzeslem systemu

Przejdz SCIEZKE KLIENTA na wlasnym telefonie (nie-firmowym):
- [ ] Wyslij zapytanie z formularza -> SMS S1 przyszedl w <60 s, kontakt w pipeline etap 1.
- [ ] Zadzwon i nie odbierz -> S2 przyszedl (jesli wlaczony).
- [ ] Zarezerwuj wizyte -> potwierdzenie + przypomnienie 24h (przestaw zegar wizyty na jutro).
- [ ] Oznacz wizyte jako odbyta -> S4 prosba o opinie przyszla, link dziala.
- [ ] Odpisz na SMS w trakcie sekwencji -> sekwencja STANELA.
- [ ] E-mail: wyslij testowy na Gmail i sprawdz folder (inbox, nie spam; jesli spam -
      sprawdz 6 rekordow DNS, najczestszy winowajca: MX bez kropki).
- [ ] Pakiet 3: automat 24/7 odpowiada na 3 typowe pytania klienta (ceny, godziny, adres)
      i NIE zmysla (AP-001/AP-003: zero obiecywania dzialan i uslug, ktorych nie ma w bazie).

## KROK 9. SZKOLENIE KLIENTA (2-4 sesje po 30-45 min, na zywo lub wideo)

Sesja 1 - Codziennosc: gdzie widzi nowe zapytania, jak odpisac, jak przesunac klienta
w pipeline, jak umowic wizyte. (Pakiet 1: to jedyna sesja + skrocona 4.)
Sesja 2 - Sekwencje: co wysyla sie samo i kiedy, jak zatrzymac, jak wyglada rezygnacja
klienta, gdzie zmienia sie tresc wiadomosci.
Sesja 3 (Pakiet 2-3) - Baza i kampanie: tagi, filtrowanie, wysylka kampanii do segmentu,
czytanie raportu miesiecznego.
Sesja 4 - Przekazanie: klucze do konta, instrukcja obslugi (nizej), co jest w gwarancji,
jak zglaszac problemy (jeden kanal: e-mail/telefon Tomasza), oferta opieki po 30 dniach.

Nagrywaj sesje (zgoda klienta) - nagranie = material szkoleniowy dla klienta + przyszly
asset produktowy.

## KROK 10. PRZEKAZANIE + OPIEKA

- [ ] Instrukcja obslugi klienta (1-2 strony, z szablonu: co robi sam / co robi system /
      kontakt awaryjny) - wersja per klient, po polsku, zero zargonu.
- [ ] 30 dni gwarancji: poprawki konfiguracji i tresci w cenie pakietu (Pakiet 3: +1 miesiac
      wsparcia = takze drobne zmiany i pytania).
- [ ] Po 30 dniach: propozycja opieki miesiecznej (przyszly cennik; na dzis: stawka godzinowa
      ustalana indywidualnie - NIE obiecuj abonamentu, ktorego jeszcze nie zdefiniowalismy).
- [ ] Wpis w naszej bazie: contacts stage='client', notatka co wdrozono; kandydat na case
      study (za zgoda) - pierwszy klient = pierwszy dowod spoleczny AGS/TNM.
- [ ] Zdejmij swoj dostep admin, jesli klient nie bierze opieki (wlasnosc = klient).

---

## ZALACZNIK: SZABLON A - wiadomosc do klienta po decyzji (zakladanie konta)

> Dzień dobry {imię},
>
> świetnie, ruszamy. Dwa kroki po Pana/Pani stronie (10 minut, robimy raz):
>
> 1. Proszę założyć konto na platformie, na której będzie działał system: {link}.
>    Wybieramy plan {Starter 97 USD / Unlimited 297 USD} - płatność kartą, bezpośrednio
>    u dostawcy. Konto jest Pana/Pani własnością, ja tylko je skonfiguruję.
> 2. Po zalogowaniu: Settings -> My Staff -> Add Employee - proszę dodać mnie jako
>    administratora: {e-mail Tomasza}. Zdejmiemy ten dostęp po wdrożeniu.
>
> Do tego poproszę: logo (najlepiej PNG), kolory firmowe (jeśli są), 3-5 zdjęć
> i dostęp do domeny (nazwa serwisu, w którym kupiona - hasła przekażemy bezpiecznie).
>
> Od momentu, gdy to dostanę, liczy się termin wdrożenia: {5-7 / 7-10 / 10-14} dni.
>
> Tomasz

## ZALACZNIK: kryteria "test krzeslem" runbooka (DoD)

Osoba znajaca GHL, ale nie znajaca klienta, jest w stanie: poprowadzic discovery z samej
listy pytan; postawic konto i fundament z krokow 2-3; skonfigurowac pipeline i sekwencje
z krokow 4-5 wybierajac wlasciwy komplet branzowy; przejsc testy z kroku 8 bez pytan
dodatkowych. Jesli ktorykolwiek krok wymaga zgadywania - poprawka runbooka, nie improwizacja.
