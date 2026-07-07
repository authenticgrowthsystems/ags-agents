# Plan testów subagentów kanałowych (07/07/2026) - wykrycie luk do budowy

**Cel:** subagent kanału (X, LinkedIn, przyszłość IG/FB) jako SPRZEDAWALNY produkt ("kup obsługę
swojego X / LinkedIn / IG"). Ten plan definiuje PEŁNY zestaw funkcji, jakie taki subagent musi mieć,
i daje testy tapnięciami z Telegrama. Dla każdego obszaru: jak testować, oczekiwane, i PRZEWIDYWANA
LUKA (z analizy kodu 07/07). Tomasz odpala, wpisuje wynik; BE mapuje na backlog budowy.

**Jak uruchomić subagenta:** Telegram -> `/agents` -> wybierz subagenta (np. Subagent AGS linkedin
albo X). Wszystkie testy = zwykłe wiadomości/pytania do niego.

**Legenda wyniku:** ✅ działa | ⚠️ działa częściowo | ❌ brak (do budowy).

---

## T1. Tożsamość i świadomość kanałów (zbudowane dziś, D)
- **Tap:** "jakie kanały obsługujesz i jaka jest strategia?"
- **Oczekiwane:** wymienia WSZYSTKIE swoje powierzchnie rodziny (LinkedIn: AGS personal aktywny,
  AGS strona/TNM/RDC czekają na aktywację) ze statusem, językiem, oknem, głosem per konto; podaje
  strategię CM (kadencja + podział ról).
- **Przewidywana luka:** powinno działać po deployu D. Sprawdzić czy nie myli statusów.

## T2. Przegląd ZAPLANOWANEJ treści + edycja  [Twoja prośba wprost]
- **Tap:** "pokaż kolejkę" / "pokaż pełną treść posta #<id>" / "chcę edytować post #<id>"
- **Oczekiwane:** pełny tekst zaplanowanej pozycji + możliwość edycji (odeślij poprawioną wersję,
  subagent podmienia), jak ✏️ Edytuj w CM.
- **Przewidywana luka: ❌** dziś subagent pokazuje kolejkę jako LISTĘ SKRÓTÓW (`_sub_queue_text`,
  ~70 zn.), ma tylko reschedule/remove po #id. BRAK: pokaż pełną treść + edytuj. **DO BUDOWY (B).**

## T3. Generowanie treści ad-hoc (voice + style bible)
- **Tap:** "zrób post na <temat>" / "napisz coś o <X>"
- **Oczekiwane:** proponuje materiał dla SWOJEGO kanału (propose_material target=[jego kanał]),
  w głosie marki (voice_bible v2.1) + wyuczony styl; przechodzi normalne zatwierdzenie.
- **Przewidywana luka:** ⚠️ propose_material jest, ale subagent = single-pass (bez pętli agentowej
  jak CM) - może utknąć jak CM przed fixem. Sprawdzić czy proponuje i pyta, czy sucho zapisuje.

## T4. Sloty, okna, kadencja + luki (autonomia)
- **Tap:** "kiedy publikujesz?" / "masz lukę w kadencji?" / poczekać na proaktywne zgłoszenie luki
- **Oczekiwane:** podaje REALNE sloty z kolejki (nie zmyśla - truth-guard); zna okno; przy luce
  sam woła CM (escalate) i przynosi propozycje.
- **Przewidywana luka:** ✅ po fixach (truth-guard slotów, proactive.check_gaps). Zweryfikować luki E2E.

## T5. Publikacja + meldunek po callbacku
- **Tap:** zatwierdź materiał -> obserwuj AGS Alerts
- **Oczekiwane:** "wysłał do publikacji (zlecone subagentowi, potwierdzę po callbacku)" -> po fakcie
  "opublikował: opublikowane <kanały>" albo "NIE POSZŁO" (per kanał).
- **Przewidywana luka:** ✅ potwierdzone dziś w AGS Alerts (fix b). OK.

## T6. Multimedia (grafika / wideo / referencje)  [Twój największy brak]
- **Tap:** "dodaj grafikę do posta #<id>" / "wygeneruj wizual" (u subagenta)
- **Oczekiwane:** subagent umie dołączyć/wygenerować grafikę lub wideo do SWOJEJ zaplanowanej pozycji.
- **Przewidywana luka: ❌** 🎨 Generuj / ➕ Media są TYLKO na kartach CM (matreview). Subagent nie ma
  narzędzi mediowych. Dodatkowo tryb awaryjny 24h publikuje z pominięciem kart -> posty bez grafik.
  **DO BUDOWY (A - osobna gałąź wizualizacyjna, patrz master prompt).**

## T7. Multi-konto routing (którą powierzchnię)
- **Tap:** "opublikuj to na LinkedIn" (mając >1 aktywne konto)
- **Oczekiwane:** pyta "personal / strona / oba?" i ustawia cel.
- **Przewidywana luka:** ⚠️ świadomość jest (D), ale realny wybór = tylko gdy >1 konto AKTYWNE;
  dziś aktywny 1 (personal). Reszta czeka na tokeny App 2 CMA. Routing dobudować przy aktywacji stron.

## T8. Język: komunikacja (PL) + publikacja (per platforma)
- **Tap:** rozmawiaj po polsku (ma odpowiadać PL); sprawdź język publikowanej treści per cel
- **Oczekiwane:** komunikacja PL (domyślnie), publikacja EN dla AGS/X/LinkedIn, PL dla TNM/RDC.
- **Przewidywana luka:** ✅ mechanizm jest (language_comm=pl default; language_publish per channel).
  Zweryfikować wartości zapytaniem (osobny test C+D) + zmiana `/set language_comm en`.

## T9. Engagement / Comment Radar (wzrost zasięgów)
- **Tap:** wklej cudzy post -> "zaproponuj komentarze"; zapytaj "co się dzieje na moim profilu?"
- **Oczekiwane:** 3 komentarze comment-first w głosie marki (suggest_comment). "Co na profilu" =
  live metryki.
- **Przewidywana luka:** ⚠️ suggest_comment działa (ręczne wklejenie). AUTO comment radar (sam szuka
  postów ICP) + live metryki = ❌ blokada: X read API płatny, LinkedIn po App 2. Do decyzji kosztowej.

## T10. Metryki + raporty dzienne/tygodniowe
- **Tap:** "raport dzienny" / "raport tygodniowy"; wpisz metryki ręcznie
- **Oczekiwane:** raport z kolejką, publikacjami, decyzjami autonomicznymi; metryki ręczne (subagent_set_metrics),
  poniedziałkowa prośba o metryki.
- **Przewidywana luka:** ⚠️ raporty + ręczne metryki są; AUTO metryki (API) = ❌ jak T9.

## T11. Tryb pracy (supervised/semi/auto) + tryb STANDALONE
- **Tap:** sprawdź czy subagent ma work_mode; czy działa samodzielnie (własny Telegram/loop) czy tylko pod CM
- **Oczekiwane (produkt):** subagent kupowany SAM (własny bot + własna pętla) LUB nadzorowany pod CM;
  work_mode autonomiczny/półautonomiczny/automatyczny per kanał.
- **Przewidywana luka: ❌/⚠️** dziś subagent = organ nadzorowany pod CM (własny czat per konto jest,
  ale własny standalone loop/bot = niezbudowany). work_mode jawny per subagent = do dopięcia. **DO BUDOWY.**

## T12. Rozmowa / kontrola profilu (jakość dialogu)
- **Tap:** swobodna rozmowa; "co masz zaplanowane i dlaczego?"
- **Oczekiwane:** partner, nie ekspedient (jak CM po fixie pętli agentowej) - własne zdanie, pyta,
  proponuje.
- **Przewidywana luka:** ⚠️ subagent NIE ma jeszcze pętli agentowej (CM ma). Jeśli w testach utyka
  na narzędziach jak CM przed fixem -> dobudować pętlę agentową też w subagencie. **PRAWDOPODOBNIE DO BUDOWY.**

---

## Podsumowanie przewidywanych LUK do budowy (przed testami)
- **B (T2):** przegląd pełnej treści + edycja u subagenta. Odblokowane, konkretne.
- **A (T6):** gałąź wizualizacyjna (grafika/wideo/referencje) - osobny agent, research-first (master prompt).
- **T11:** tryb standalone subagenta (własny bot/loop) + jawny work_mode = sprzedawalność "kup sam kanał".
- **T12:** pętla agentowa w subagencie (jakość dialogu jak w CM).
- **T7/T9/T10 (częściowo):** routing multi-konto (po aktywacji stron) + live metryki/comment radar
  (decyzja kosztowa o API).

## Definicja produktu (kotwica sprzedaży)
"Kupujesz obsługę swojego X / LinkedIn / IG": subagent planuje i generuje treści w Twoim głosie
(voice+style bible), dokłada grafikę/wideo, publikuje w oknach strefy odbiorców, pilnuje kadencji,
komentuje pod ICP, raportuje z metrykami, i rozmawia z Tobą po polsku. Kupowany SAM albo w pakiecie
z Content Managerem. CM SAM (bez subagentów) planuje kolejkę i generuje treści z bibli głosu/stylu.
