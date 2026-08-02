# AP-309: Poprawka w JEDNYM miejscu, gdy ta sama wada zyje w wielu

**Ustanowiony 25/07/2026 (Manager AGS, przy zleceniu Voice Bible v2.2).** Blizniak AP-307
(tam: nowy kontrakt bez przelaczenia zywych konsumentow). Tu: NAPRAWA/ZMIANA zrobiona w jednym
miejscu, podczas gdy ta sama wada albo ten sam odczyt zyje w wielu miejscach naraz.

**Dowody (jeden tydzien, cztery przypadki tej samej klasy):**
1. **Glos ucinany 9x** (24/07): `voice_bible[:1200..3000]` w dziewieciu miejscach, nie jednym.
   Zgloszenie Managera dotyczylo JEDNEGO slice; grep pokazal dziewiec.
2. **Skala tierow przepisana 4x** (24/07): dodanie 'Inne' wymagalo czterech spojnych edycji
   (dwie karty, prompt wizji, mapa parsera) - przy piatym miejscu ktos by przeoczyl.
3. **Cichy except 19x** (24/07): P5 Managera - regula "cichy except = blad" dotknela 19 miejsc.
4. **Auto-grafika w 2 torach** (25/07): wylaczenie wymagalo obu (przed karta + dispatch), nie
   jednego.

**Dlaczego zle:** poprawka wygladajaca na kompletna zostawia te sama wade w pozostalych
miejscach. Przy odczycie wspoldzielonej wartosci (voice_bible, skala tierow) rozjazd jest cichy
- jedno miejsce dziala nowa wersja, inne stara. Testy syntetyczne tego nie lapia, bo sprawdzaja
zmienione miejsce.

**Poprawnie:**
1. **Zanim uznasz poprawke za zrobiona, policz GREPEM, ile miejsc ma te sama wade albo czyta
   te sama wartosc.** Nie zakladaj, ze jedno. `grep -rn '<wzorzec>' --include=*.py`.
2. **Sprowadz do JEDNEGO zrodla, gdy to mozliwe** - `crm.TIERS`/`TIER_OPTIONS` (skala tierow),
   `brand.voice_block` (glos). Wtedy nastepna zmiana dotyka jednego miejsca, nie N.
3. **Przy wgrywaniu wspoldzielonej wartosci** (np. voice_bible do brand_config) sprawdz WSZYSTKIE
   loadery - czy zaden nie tnie, nie hardkoduje, nie czyta osobno. Voice Bible v2.2: trzy loadery
   (`brand.voice_block`, `conversation` dyskusja CM, `sales` outreach), wszystkie przez
   `load_brand -> brand['voice_bible']` pelne, wiec jedna zmiana w bazie dociera do wszystkich.
4. **Blok prompt-cache (`voice_block`) MUSI zostac bajtowo staly** dla danej wersji - inaczej
   pamiec podreczna promptu przestaje trafiac. Zmienne (data, stan kolejki) ida do wiadomosci
   uzytkownika, NIGDY do bloku glosu.

---

## ROZSZERZENIE 02/08/2026: ta sama wada od strony SZUKANIA, nie naprawy

**Ustanowione przez Tomasza po znalezisku w politykach prywatnosci TNM.**

Dotad AP-309 mowil: policz grepem, ile miejsc ma te sama wade. To za malo. **Grep na JEDNA FRAZE
zanizza liczbe trafien, kiedy dwa dokumenty mowia to samo INNYMI SLOWAMI.**

**Dowod (02/08/2026, dwa pliki polityki prywatnosci):** ten sam falsz - "serwis nie uzywa
analityki" przy dzialajacym od 30/05 GA4 - wystepowal w dwoch plikach w czterech miejscach,
i za kazdym razem inaczej sformulowany:

| plik | sformulowanie |
|---|---|
| `TNM_Polityka_Prywatnosci_v1.md` sekcja 6 | "nie uzywa cookies analitycznych ani marketingowych" |
| `TNM_Polityka_Prywatnosci_v1.md` sekcja 7 | "Google Analytics **(w przyszlosci)** - 26 miesiecy" |
| `GHL_Build_v3\pages\polityka-prywatnosci.md` sekcja 6 | "**brak Google Analytics, Facebook Pixel w Wave 0**" |
| `GHL_Build_v3\pages\polityka-prywatnosci.md` sekcja 7 | "GA4, **gdy wdrozone Wave 1+**" |

Grep frazy z pierwszego pliku ("nie uzywa cookies analitycznych") zwrocil **jedno** trafienie.
Prawdziwych bylo **cztery**. Dwa ostatnie znalazlem dopiero przy kontroli koncowej, przypadkiem -
bo szukalem juz innej rzeczy.

**ZASADA: przy szukaniu tego samego falszu w wielu plikach szukaj POJECIA, nie FRAZY.**
Minimum **trzy rozne sformulowania**, zanim uznasz, ze plik jest czysty.

W praktyce dla przykladu powyzej wzorzec musial objac naraz: `analitycz`, `Google Analytics`,
`GA4`, `Wave 0`, `Wave 1`, `w przyszlosci`, `Pixel`. Zaden pojedynczy nie wystarczyl.

**Powiazanie z AP-313:** tam pulapka byla w znakach (ogonek w srodku slowa), tu w slowach
(synonim zamiast frazy). Wspolny mianownik: **wzorzec dopasowania jest zalozeniem o danych,
a nie faktem o nich** - i jak kazde zalozenie, wymaga sprawdzenia.
