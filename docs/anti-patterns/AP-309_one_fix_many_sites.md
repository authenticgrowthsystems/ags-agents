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
