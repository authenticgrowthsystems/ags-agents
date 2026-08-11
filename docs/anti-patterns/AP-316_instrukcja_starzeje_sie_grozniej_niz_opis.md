# AP-316: Dokument, ktory INSTRUUJE, starzeje sie grozniej niz dokument, ktory OPISUJE

**Ustanowiony 11/08/2026 (Manager AGS, po przegladzie gotowosci repo).**
Rodzina AP-312 na poziomie dokumentacji: tam etykieta stanu obiecuje co innego, niz znaczy;
tu **instrukcja kaze odtworzyc awarie i wyglada przy tym swiezo**.

## Wzorzec

Dokumentacja starzeje sie zawsze. Ale nie kazde starzenie kosztuje tyle samo:

| rodzaj dokumentu | co robi nieaktualny | koszt |
|---|---|---|
| **OPIS** ("system dziala tak") | wprowadza w blad | czytajacy traci czas, potem sprawdza w kodzie |
| **INSTRUKCJA** ("zrob tak") | **kaze WYKONAC stare zachowanie** | wykonawca odtwarza awarie, ktora juz raz zaplacilismy |

Instrukcja nie ma przy sobie ostrzezenia. Wyglada dokladnie tak samo w dniu napisania
i trzy miesiace pozniej - i **jest wykonywana**, a nie tylko czytana.

## Dowod: przeglad gotowosci repo 11/08/2026

Trzy dokumenty, zaden nieoznaczony jako nieaktualny:

1. **`DEPLOY_CHECKLIST.md`** (playbook instalacji U KLIENTA) kazal ustawic
   `publish_mode='webhook'` - tryb **zabroniony od 22/07** po incydencie AP-307
   (4-5 postow X w godzine, zgubione media, polski post na anglojezycznym profilu,
   baza klamiaca o stanie). Kazal tez zaaplikowac migracje "001..008", gdy jest ich **42** -
   swieza instalacja dostalaby jedna piata schematu.
   **To nie jest dokument do czytania. To jest lista, ktora ktos WYKONA krok po kroku
   u nowego klienta.**
2. **`README.md`** wymienial katalogi `skills/` i `mcps/`, ktore nie istnieja, a milczal
   o `cm-agent/` - czyli o CALYM systemie. Status z 19/05 mowil, ze X Agent jest zaparkowany,
   a LinkedIn w backlogu; oba sa od miesiecy jedynymi zywymi kanalami.
3. **`SYSTEM_DATAFLOW.md`** podawal "ostatni zaaplikowany DDL: 029" przy faktycznych **042**.

Anty-wzorzec AP-307 byl **zapisany** 20/07, komponent poprawiony, produkcja przelaczona -
a instrukcja instalacji przez trzy tygodnie dalej uczyla starego zachowania. Nikt nie klamal.
Po prostu nikt nie sprawdzil, czy gdzies indziej stoi zdanie rozkazujace.

## Why bad

- **Instrukcja jest WYKONYWANA, nie oceniana.** Wykonawca (instalator, nowy programista,
  agent) zaklada, ze skoro jest w repo, to obowiazuje. Nie ma powodu jej kwestionowac.
- **Nieaktualnosc jest niewidoczna z zewnatrz.** Dokument nie ma stanu. Wyglada tak samo
  swiezo w dniu, w ktorym przestal byc prawdziwy.
- **Poprawka kodu nie propaguje sie sama.** Kod poprawiasz, bo pamietasz, gdzie mieszka.
  Instrukcje mieszkaja gdzie indziej i **nikt ich nie kompiluje** - nie ma testu, ktory by padl.
- **Koszt jest zewnetrzny.** Awarie z nieaktualnej instrukcji placi klient albo nowy czlonek
  zespolu, nie autor.

## Correct

1. **Po zapisaniu anty-wzorca albo zmianie zachowania: `grep` po dokumentach INSTRUKTAZOWYCH**
   (playbooki, runbooki, README, przewodniki wdrozeniowe) i sprawdz, czy ktorys nadal uczy
   starego. Nie po dokumentach opisowych - te znajdzie sie przy nastepnym czytaniu.
2. **Dokument instruktazowy nosi DATE WERYFIKACJI, nie date powstania**, i regule w naglowku:
   "przy zmianie zachowania X ten plik zmienia sie w TYM SAMYM commicie".
   `DEPLOY_CHECKLIST` v3 ma to od 11/08.
3. **Instrukcja podaje POLECENIE, nie liczbe zapamietana z przeszlosci.**
   `ls cm-agent/db/*.sql | sort` zamiast "001..042" - liczba znowu sie zestarzeje, polecenie nie.
4. **Krok, ktory jest zabroniony, ma miec przy sobie POWOD i odeslanie do anty-wzorca**,
   zeby nastepny czytajacy nie cofnal go w dobrej wierze.
5. **Najmocniejsze: zamien warunek zapisany w dokumencie na blokade w KODZIE, gdy tylko sie da.**
   Warunek w dokumencie jest zalozeniem (AP-314). Decyzja Managera 11/08 przy AP-307:
   `publish_mode='webhook'` ma padac glosno w kodzie, z komunikatem wskazujacym anty-wzorzec.

## Punkty zaczepienia

- `DEPLOY_CHECKLIST.md` v3 - naglowek z data weryfikacji i regula wspolnego commita
- `docs/anti-patterns/AP-307_nowy_kontrakt_bez_przelaczenia_konsumenta.md` - sekcja
  "zapisany anty-wzorzec nie jest wdrozonym anty-wzorcem"
- `docs/cm/RAPORT_do_Managera_11082026_gotowosc_repo.md` sekcja 2 - trzy dokumenty z dowodami
