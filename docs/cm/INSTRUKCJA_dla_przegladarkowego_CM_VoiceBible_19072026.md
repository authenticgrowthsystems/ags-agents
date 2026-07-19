# INSTRUKCJA dla przegladarkowego CM: Voice Bible po decyzji Tomasza (19/07/2026)

(Tomasz: wklej to przegladarkowemu CM albo wrzuc do jego kontekstu.)

Decyzja Tomasza 19/07: **zrodlem prawdy glosu jest brand_config w PostgreSQL, nie Notion.**

1. Twoja strona "VOICE BIBLE - Tomasz Nawrocki (CANONICAL)" (331c00c9...) jest od teraz
   READ-ONLY MIRROREM. NIE edytuj jej. Rdzen DNA (sekcje 1-8) zyje w brand_config jako
   `voice_dna_core` i bedzie odbijany na te strone automatycznie.
2. **Sekcja 9 "Waluta i jezyk per marka" JEST NIEWAZNA.** Obowiazuje nowszy kanon
   (AGS Voice Bible v2.2, sekcja 15, canonical 12/07):
   - AGS = USD, TNM = PLN dla CEN I OFERT marki;
   - **fakty zrodlowe ZAWSZE w ich walucie** (rachunek byl w PLN = piszesz PLN, takze
     w tresci EN) - ZERO mechanicznego przeliczania faktow;
   - benchmark cross-market wolno przeliczyc TYLKO z jawnym oznaczeniem (~, "okolo");
   - waluta zawsze explicite ($ / PLN / zl), zero golych liczb przy kwotach.
   Do tego sekcja 14 (barwy per marka) tez zyje w brand_config, nie u Ciebie.
3. Nowe reguly glosu zglaszasz Tomaszowi; wchodza przez bump w brand_config (wersja+md5+
   historia). Dopisywanie zasad w Notion = rozjazd i incydenty (dzis: sprzeczna regula
   walutowa prawie weszla do artykulow dual-brand).
