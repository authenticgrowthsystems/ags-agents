# Anti-Pattern Library

Lessons learned across all AGS agents. Each entry: anti-pattern + why bad + correct alternative.

Agents must screen output against this library BEFORE HITL preview.

---

## Voice / Conversation Anti-Patterns (from Pawel Voice Agent tests #1-7)

### AP-001: Hallucinating actions you don't have
**Anti-pattern:** "Wyślę Panu SMS-a z potwierdzeniem" when no SMS workflow exists.
**Why bad:** Customer waits for SMS that never arrives. Trust killer.
**Correct:** "Tomasz oddzwoni najszybciej jak to możliwe. Zapisałem Pana dane."

### AP-002: Information dump on closed questions
**Anti-pattern:** Customer asks "Czy macie półkolonie?" → Agent gives 8-sentence lecture on dates, prices, program, age groups.
**Why bad:** Closed question wants Yes/No + qualifying question, not unsolicited deep dive.
**Correct:** "Tak, mamy. Dla jakiego dziecka?" Max 2 sentences. Let customer drive depth.

### AP-003: Hallucinating offering names
**Anti-pattern:** Inventing classes like "Hip Hop Juniorzy" when KB lists "Hip-Hop dla Dzieci (8-12 lat)".
**Why bad:** Customer expects offering that doesn't exist. Trust + brand consistency damage.
**Correct:** Use exact KB names. If category not in KB: "Tej kategorii nie mamy. Tomasz oddzwoni z propozycją alternatywy."

### AP-004: Continuing conversation after farewell
**Anti-pattern:** After saying "Dziękuję za telefon, do usłyszenia" - agent adds "Czy mogę kontynuować?"
**Why bad:** Logical drift. Disrespects customer's signal that they're done.
**Correct:** After farewell = END. No more questions, no more topics.

### AP-005: Reading domain names literally
**Anti-pattern:** "Proszę wejść na royaldance.pl" (TTS pronounces poorly).
**Why bad:** TTS distortion makes customer think you said something else.
**Correct:** "Nasza strona internetowa" or "przez naszą stronę". Only literal if customer explicitly asks for URL.

### AP-006: Phone numbers grouped wrong
**Anti-pattern:** "sześćset dwadzieścia, dwa dziewięć, osiemset pięćdziesiąt cztery" (grouping into numbers).
**Why bad:** Customer can't follow / verify. Polish mobile is 9 digits in 3+3+3 pattern.
**Correct:** Single digit per beat with pauses. "sześć, dwa, zero. [pauza] dwa, dziewięć, osiem. [pauza] pięć, cztery, dziewięć"

### AP-007: Price-first communication
**Anti-pattern:** "Pakiet Premium kosztuje 1990 zł. W nim 8 spotkań."
**Why bad:** Customer hears price before understanding value. Defensive reaction.
**Correct:** "Para przed weselem ma 3 miesiące, pierwszy raz tańczy. Rozwiązanie: 8 spotkań, montaż muzyki, próba na sali. Rezultat: pewność na parkiecie. Inwestycja: tysiąc dziewięćset dziewięćdziesiąt złotych."

### AP-008: "Bezpłatne" instead of "niezobowiązujące"
**Anti-pattern:** "Pierwsze zajęcia są bezpłatne."
**Why bad:** If customer stays, first class becomes part of monthly fee - "bezpłatne" was technically misleading.
**Correct:** "Pierwsze zajęcia są niezobowiązujące."

---

## Content Anti-Patterns (from 23 Manager chats + brand canon learnings)

### AP-101: Em dashes
**Anti-pattern:** Using em dash (—) anywhere in any AGS content.
**Why bad:** Tomasz brand canon RULE 1.
**Correct:** Hyphen, restructure sentence, or use colon.

### AP-102: Empty enthusiasm vocabulary
**Anti-pattern:** "Fantastycznie!", "Wspaniale!", "Doskonale!", "Świetnie się składa!"
**Why bad:** Empty filler, doesn't convey real reaction, sounds AI-generated or corporate.
**Correct:** "Super.", "Dobrze.", "Jasne.", "Rozumiem."

### AP-103: Promising scarcity that doesn't exist
**Anti-pattern:** "Tylko 3 miejsca zostały!" when no inventory check happened.
**Why bad:** Fake urgency damages brand long-term.
**Correct:** State real availability or skip urgency.

### AP-104: Generic stock photos in content
**Anti-pattern:** Using stock founder photos / generic AI workspace shots for AGS content.
**Why bad:** AGS positioning is "real builds in public" - stock images undermine authenticity.
**Correct:** Real screenshots from current builds, raw phone photos, even messy whiteboards.

---

## Strategic Anti-Patterns

### AP-201: System-building before understanding what produces revenue
**Anti-pattern:** Spending weeks on infrastructure that doesn't connect to client conversion.
**Why bad:** Stage 0-1 + Hormozi 10-Stage doctrine.
**Correct (pre-19/05):** "No system building before first sale."
**Correct (post-19/05 pivot):** "System building IS content IS revenue activity - but only when build is documented in public AND links to ICP attraction."

### AP-202: Lowering price after customer says no
**Anti-pattern:** "Premium is 1990 zł. (customer hesitates) Actually I can do 1500 zł for you."
**Why bad:** Trains customer to push back on every price. Damages anchor.
**Correct:** Down-tier to a different package (Startowy 880 zł) instead of discounting same package.

### AP-203: Maintaining 50 KPIs
**Anti-pattern:** Dashboard with 30+ metrics nobody acts on.
**Why bad:** Cognitive overhead, dilutes focus, paralyzes action.
**Correct:** Max 3 KPIs per stage. Default: Revenue (closed $), Pipeline (calls booked), Close rate (%).

### AP-301: New n8n node with typeVersion from memory instead of from a working sibling
**Anti-pattern (03/07/2026, BE, HITL 1b build):** created two IF nodes with `typeVersion: 1` but NEW filter-format conditions. Old IF engine ignores the unknown format and passes EVERYTHING true - the agent router silently sent all text to Idea Bot and (worse) the agsel gate swallowed ALL callback families, killing approve/triage buttons until hotfix.
**Why bad:** silent pass-through, no error anywhere; discovered only in Tomasz's tap-test; every broken production window costs trust and money.
**Correct:** when adding a node to an existing workflow, COPY typeVersion + parameter shape from a WORKING node of the same type in that workflow (e.g. `Is Cm Callback?` = if 2.2, conditions.options {version:2, typeValidation:'loose'}). Verify routing with a real execution read (executions API, node-by-node), not only structure.

### AP-303: SQL string literals in generated ETL without dollar-quoting
**Anti-pattern (05/07/2026, BE, #71 Faza B):** generator built an INSERT with a Polish doctrine text embedded via `'...'` and manual `''` escaping of only SOME apostrophes - the canonical-bio INSERT failed live (`syntax error at or near "choreograf"`) while 20 sibling INSERTs (escaped via helper) passed, so the miss was silent until psql output was read line-by-line.
**Why bad:** hand-escaping free text is guaranteed to miss quotes eventually; a failed statement inside a multi-statement file does NOT stop the file, so partial loads look successful.
**Correct (canonical, Manager 05/07 - applies to ALL future AGS/client migrations and ETL):** EVERY free-text literal in generated SQL goes through dollar-quoting (`$tag$...$tag$` with an `assert tag not in text` guard) or bind parameters; never hand-escaped quotes. Verify loads by row-count SELECT, not by absence of visible errors.

### AP-304: Generated INSERTs into an existing table without reading its CHECK constraints first
**Anti-pattern (05/07/2026, BE, #71 Faza C - TWICE in one day):** task_queue import failed on `task_type_check` ('notion_task' not allowed), then contacts import failed on `icp_tier_check` (source page used long labels "Premium $2K+" while the schema enum is short 'Premium'). Column names/types were audited, constraints were not.
**Why bad:** CHECK violations kill every row silently row-by-row in multi-statement files; source-document labels rarely match schema enums verbatim.
**Correct:** before generating INSERTs into ANY existing table, dump `pg_get_constraintdef` for its CHECKs and map source labels onto the allowed values (or extend the CHECK via reviewed DDL when the new value is semantically new). Add the mapping to the ETL report.

### AP-305: Notion 404 treated as a bad page ID instead of missing integration access
**Anti-pattern (05/07/2026, BE, #71 Faza D):** ETL engine got `404 Not Found` on 3 GHL pages whose IDs were verified via MCP fetch the same day. Root cause: Notion API returns 404 also when the page EXISTS but the integration token has no Connection to its tree - MCP uses the USER's permissions (whole workspace), the `ntn_` token sees only explicitly connected page trees. Extra trap: the workspace has 3+ integrations (n8n-TNM, n8n-AGS, AGS Automation) - the Connection must go to THE integration whose key sits in app_secrets.
**Why bad:** looks identical to a wrong ID; chasing IDs wastes paid attempts while the fix is one click in Notion UI.
**Correct:** before adding ETL sources from a new page tree, add the integration Connection on that tree's root (inherits to children). Diagnose 404 from evidence: `GET /v1/users/me` with the vault token (bot name = which integration to look for in Connections) + `GET /v1/pages/{id}` http_code. "MCP sees it" never implies "the ETL token sees it".

### AP-306: One-shot container assumes worker-loaded secrets and fails silently
**Anti-pattern (05-06/07/2026, BE, TWICE):** `drift_check` sent Telegram alerts into the void (log_bot_token not loaded) and `bulk_polish` "corrected" 37 texts while every LLM call silently failed (anthropic_api_key not loaded) - one-shot `docker run` containers skip `worker._load_secrets`, env carries only POSTGRES_DSN.
**Why bad:** success-shaped output while doing nothing; false confidence, invisible user-facing gap.
**Correct:** every one-shot `python -m app.<tool>` loads its own required keys from app_secrets at top of main() and fails LOUDLY when one is missing; grep new one-shots for `config.*KEY|TOKEN` usage and cover each.
**Rozszerzenie kanonu 24/07/2026 (decyzja Managera P5): CICHY `except` TO BLAD PROJEKTOWY.** Trzeci przypadek tej klasy bez kontenera jednorazowego: `Decimal` w payloadzie meldunku Researchera wywracal INSERT, wyjatek byl polykany, a joby konczyly sie 'completed' z 11 faktami i ZEREM powiadomien (91d8b597, b55a9f58) - praca wykonana i zaplacona, nikt sie nie dowiedzial. Regula: `except: pass` wolno TYLKO gdy cisza jest zamierzona i wyjasniona komentarzem w tej samej linii (timeout nasluchu, parsowanie znacznika z wartoscia domyslna); na sciezce powiadamiania, zapisu wyniku albo NAUKI - minimum `traceback.print_exc()`, a przy powiadomieniu czlowieka ESKALACJA. Przeglad wykonany 24/07: 17 miejsc uglosnione, 2 zostawione cicho z uzasadnieniem. Test dymu importow: `cm-agent/tests/test_import_smoke.py`. Pelny opis: docs/anti-patterns/AP-306_oneshot_container_secrets.md.

### AP-307: New contract built without switching/verifying the live consumer of the old one
**Anti-pattern (20/07/2026, BE, publication incident):** the whole slot machinery was built (humanize_slot, series with consecutive slots, Scheduler `WHERE scheduled_for <= NOW()`), but `channels.config.publish_mode` stayed 'webhook' - the live delegate path publishes INSTANTLY at dispatch and ignores slots entirely. Result: 4-5 X posts fired within one hour, media attached to rows were lost (delegate contract has no chunked upload), a Polish post went out on the English-only LinkedIn profile, and the X callback marked ALL item rows 'published' - including rows with slots hours in the future - so the DB lied about system state. Tomasz's framing to record: "jak cos dziala to po co to zmieniac jak budujesz cos innego" is FALSE when the new build changes a contract the old path consumes.
**Why bad:** every symptom looked like a fresh bug in the NEW code, while the new code was correct and bypassed; falsified DB state ('published' with future slots) poisons every later diagnosis; public-facing damage (burst, wrong language) before anyone can react.
**Correct:** when a build changes a contract (slots become meaningful, language becomes per-channel), enumerate EVERY live path consuming that contract (here: publish_mode per channel + publisher callbacks) and switch or verify each IN THE SAME BUILD; end with an end-to-end probe through the path that will actually run in production, not the path you just wrote.

### AP-308: Masowa zmiana zywych danych bez DETERMINISTYCZNEGO podgladu
**Anti-pattern (25/07/2026, BE, re-slotter kolejki X):** skrypt zmienial scheduled_for 64 wierszy zywej kolejki naraz. Dry-run zlapal DWA bledy, ktore apply wypuscilby na produkcje: (1) v1 rozproszyl serie (nadmiar kaskadowal po chronologii, hook po rozwinieciu), (2) stala siatka gniazd nie miescila sie w oknie kanalu 13-22, wiec wyszlo 3/dzien zamiast 5 i kolejka rozwleczona do 15/08. Publikacja jest wychodzaca i nieodwracalna - zly apply psulby ja przez dni.
**Why bad:** blad algorytmu przydzialu jest niewidoczny w kodzie i w testach syntetycznych; ujawnia sie dopiero na PELNYCH prawdziwych danych (prawdziwe okno, prawdziwe id serii, skala 64 nie 15 - stan gry ucinal widok do 10).
**Correct:** kazda masowa zmiana zywych danych = tryb DRY-RUN drukujacy DOKLADNIE to, co zrobi apply (czlowiek zatwierdza, potem apply); wynik DETERMINISTYCZNY (losowosc jak humanize_slot -> apply != dry; re-slotter dostal _human_minute per id); idempotencja jako test (drugi przebieg = 0 zmian); nie hardkoduj tego, co w configu (godziny vs publish_windows); nie zakladaj skali - pobierz pelny zbior. Pelny opis: docs/anti-patterns/AP-308_bulk_write_needs_deterministic_dry_run.md.

### AP-309: Poprawka w JEDNYM miejscu, gdy ta sama wada zyje w wielu
**Ustanowiony 25/07/2026 (Manager AGS).** Blizniak AP-307 od strony NAPRAWY. Jeden tydzien, cztery przypadki tej klasy: glos ucinany 9x (voice_bible[:N] w dziewieciu miejscach, nie jednym), skala tierow przepisana 4x (dodanie 'Inne'), cichy except 19x (P5), auto-grafika w 2 torach. **Why bad:** poprawka wygladajaca na kompletna zostawia te sama wade w pozostalych miejscach; przy odczycie wspoldzielonej wartosci rozjazd jest cichy (jedno miejsce nowa wersja, inne stara), testy syntetyczne tego nie lapia. **Correct:** zanim uznasz poprawke za zrobiona, policz GREPEM ile miejsc ma te sama wade (`grep -rn`); sprowadz do JEDNEGO zrodla gdy mozliwe (crm.TIERS, brand.voice_block); przy wgrywaniu wspoldzielonej wartosci sprawdz WSZYSTKIE loadery; blok prompt-cache MUSI zostac bajtowo staly dla wersji. Pelny opis: docs/anti-patterns/AP-309_one_fix_many_sites.md.

### AP-312: Nazwa stanu albo tresc etykiety obiecuje cos innego, niz znaczy
**Ustanowiony 29/07/2026 (Manager AGS).** Blizniak AP-311, ale ODWROTNY: tam widok MILCZY o stanie, ktory baza zna; tu widok MOWI - i mowi cos innego, niz jest. **Nazwa jest dana tak samo jak liczba, i tak samo moze klamac.** Stan dostaje nazwe, ktora jest skrotem myslowym AUTORA; kazdy inny czyta samo slowo i wyciaga wniosek zgodny z jego potocznym znaczeniem - wniosek RACJONALNY i FALSZYWY. **Cztery przypadki z jednego tygodnia:** (1) "⚠️ BRAK nastepnego kroku" znaczylo naraz "nie wiem, co dalej" i "jeszcze nie pisalismy" - wlasny Agent Sprzedazy zaproponowal uspienie osiemnastu prospektow jako "martwego ciezaru", czyli to, co wlasciciel odrzucil tego samego dnia rano; (2) `dispatching` brzmi jak "wysylam", a znaczy "czekam az wszystkie wiersze serii sie domkna" - siedem zdrowych materialow, najstarszy 51 godzin i poprawnie; (3) karta decyzji z zywymi guzikami przy bramce wygaszonej dobe wczesniej, siedem prawie identycznych kart i zaden sposob odroznienia zywej; (4) `rejected` nieodroznialny miedzy wycofaniem hurtowym 21 materialow a odrzuceniem przy przegladzie miesiac temu (zapytanie zwraca 26, z operacji jest 21). **Why bad:** blad jest niewidzialny dla OBU stron - autor nazwy nie widzi problemu, bo dla niego nazwa jest oczywista, czytajacy nie widzi, bo wyciagnal poprawny wniosek z tego, co przeczytal; skaluje sie z liczba agentow czytajacych te sama baze; testy tego nie lapia, bo nie ma czego asertowac. **REGULA OPERACYJNA:** przy kazdej nowej etykiecie stanu zadaj jedno pytanie, ZANIM ja nazwiesz - czy ktos, kto zobaczy to slowo bez dostepu do kodu, zrozumie je tak samo jak ja. Jesli nie, to nie jest nazwa, tylko skrot dla autora. Praktycznie: jedna etykieta = jedno znaczenie; nazwa ma oddawac czas trwania; stan wygaszony musi wygladac na wygaszony TAKZE poza baza; operacja hurtowa ma zostawiac slad, ktory ja identyfikuje. Pelny opis: docs/anti-patterns/AP-312_nazwa_stanu_klamie.md.

### AP-311: Brak danych to nie fakt o swiecie, dopoki nie sprawdzisz, czy system mial jak je pokazac
**Ustanowiony 27/07/2026 (Manager AGS).** Blizniak AP-309 od strony DIAGNOZY. Pustka w widoku ("brak kontaktu", "zero wysylek") ma DWIE mozliwe przyczyny i tylko jedna jest faktem o swiecie: albo danych naprawde nie ma, albo sa, ale system nie mial ich jak pokazac. **Trzy przypadki w jednym tygodniu:** (1) Voice Bible - Manager oczekiwal version=4, sonda pokazala, ze czworke zajela stara v2.2; (2) StandART - pamiec projektu mowila "gotowiec wyslany 24/07", sonda: siedem `proposed`, ZERO `sent`; (3) dwanascie odrzuconych duplikatow - lejek pokazywal "brak kontaktu" przy dziewieciu prospektach i zapadla decyzja o parkowaniu, a mail i telefon kazdego z nich lezaly w pliku na dysku Tomasza od 23/07 (import wyrzucal je pytajac tylko "czy nazwa jest w lejku", nie "czy wnosi cos, czego lejek nie ma"). **Why bad:** decyzja wyglada na ugruntowana w danych, wiec nikt jej nie kwestionuje; wina laduje na czlowieku ("zaniedbane prospekty") zamiast na systemie ("nigdy nie podal adresow"); pustka jest cicha - brakujaca kolumna nie rzuca wyjatku, a filtr, ktory cos wyciol, wyglada jak filtr, ktory nie mial czego wyciac. **Correct:** zanim uznasz brak za fakt, zadaj trzy pytania - czy istnieje droga zapisu, czy istnieje odczyt, czy jakis filtr mogl to wyciac; kazdy filtr ma raportowac ILE i DLACZEGO odrzucil; duplikat nie jest smieciem (moze niesc pola, ktorych docelowy wiersz nie ma); kolumna bez drogi zapisu jest martwa (who_is_who zylo tak cztery dni); **gdy stan w glowie rozjezdza sie ze stanem w bazie, wygrywa sonda**. Pelny opis: docs/anti-patterns/AP-311_brak_danych_to_nie_fakt.md.

### AP-310: Straznik z LIMIT-em PRZED odsiewem zaglodzi sie na wlasnych zaleglosciach
**Ustanowiony 26/07/2026 (BE, diagnoza lejka).** Rodzina AP-308 od strony ODCZYTU. Cykliczny straznik pobieral zaleglosci przez `ORDER BY created_at LIMIT 5`, a wiersze z otwarta juz bramka odsiewal dopiero w Pythonie przez `continue`. **Dowod produkcyjny:** siedem wierszy StandART czekalo ponad dobe, piec najstarszych mialo bramki #152-156, wiec straznik bral piatke, odsiewal ja w calosci i konczyl przebieg z zerem - a poniewaz sortuje od najstarszych, blokada nie miala jak sie rozejsc. Zamilkl przy tym CALY comment-radar (ten sam organ obsluguje komentarze i DM-y), podczas gdy dokumentacja komponentu obiecywala "Nic nie ginie". Wada zyla w dwoch miejscach naraz (AP-309). **Why bad:** awaria jest cicha (zero wyjatkow; licznik zero wyglada jak "brak zaleglosci"), trwala (najstarsze zostaja w puli w kazdym kolejnym przebiegu) i rozlewa sie na sasiadow korzystajacych z tego samego zapytania. Testy syntetyczne jej nie lapia, bo przy dwoch wierszach i limicie piec problem nie istnieje. **Correct:** odsiew (`NOT EXISTS`) nalezy do ZAPYTANIA, przed `LIMIT`; limit to dlawik wyjscia, nie wejscia; przy kazdym strazniku z limitem zadaj pytanie "co, jesli wszystkie N sa zablokowane"; najpierw domknij ZRODLO wiecznych pozycji, potem popraw straznika - odwrotnie to zamiatanie objawu. Pelny opis: docs/anti-patterns/AP-310_watchdog_limit_before_filter.md.

### AP-302: User-facing vocabulary invented by the agent without checking brand register
**Anti-pattern (03/07/2026):** BE named the inspirations pool "zanadrze" in bot replies and tool names. Tomasz: "na pewno nie bedziemy tego slowa uzywac".
**Why bad:** user-facing wording is brand voice territory; archaic/bookish words break the operator register.
**Correct:** for user-facing labels pick plain everyday Polish ("schowek", "baza"), confirm with Tomasz when introducing a NEW recurring label.

### AP-313: Zalozenie ASCII przy polskich nazwach wlasnych
**Ustanowiony 01/08/2026 (Manager AGS), podniesiony do kanonu 02/08.** Zlapany na wlasnym kodzie kilka godzin po tym, jak ten sam kod przeszedl komplet testow i wdrozenie. Piszac dopasowanie po nazwie wlasnej, autor swiadomie unika literalu z polskim znakiem (kodowanie w drodze potrafi je przekrecic) i wycina "bezpieczny" fragment ASCII. **Pulapka: ogonek potrafi siedziec w SRODKU tego fragmentu.** `ILIKE '%Chwalin%'` dla nazwy **Chwaliński** nie trafia NIGDY - w tym slowie nie ma zwyklego `n`; bezpieczny fragment to `Chwali`, i widac to dopiero, gdy sie przeliteruje. **Why bad:** PIERWSZY przebieg dziala poprawnie (`WHERE NOT EXISTS (... ILIKE ...)` przy pustej bazie zwraca prawde, wiersz sie zaklada, test akceptacyjny przechodzi), a defekt wychodzi dopiero przy DRUGIM uruchomieniu jako duplikat - przy czym zapytanie kontrolne na koncu tego samego pliku uzywalo TEGO SAMEGO wzorca, wiec bylo slepe tak samo. **Zdanie kanoniczne (Manager 02/08): "Narzedzie do wykrycia bledu mialo ten sam blad".** Bije tez poza SQL: katalog klienta na dysku nazywa sie `Chwalinski`, a wiersz w lejku **Chwaliński** - most dysk-baza pekalby, wygladajac jak "nie ma takiego klienta". Rachunek AP-309: siedem podatnych dopasowan (`sales.py` 225/1178/1730, `teczka.py` 69/76/106/109). **Correct:** normalizuj OBIE strony (`translate(...)`, ewentualnie `unaccent`); nigdy nie zakladaj, ze da sie "obciac przed ogonkiem" (w polskich nazwiskach ogonek siedzi zwykle w srodku); zapytanie kontrolne MUSI uzywac INNEGO mechanizmu niz operacja (RUNBOOK punkt 6). Pelny opis: docs/anti-patterns/AP-313_zalozenie_ascii_przy_polskich_nazwach.md.

### AP-314: Bramka bezpieczenstwa, ktorej nikt nie widzial przy pracy, jest zalozeniem
**Ustanowiony 03/08/2026 (BE, w trakcie okna migracyjnego D-008).** Rodzina AP-311, ale skierowana DO WEWNATRZ: tam brak DANYCH brany za fakt o swiecie, tu **cisza wlasnego zabezpieczenia brana za dowod, ze nie bylo czego zglaszac**. Sciezka bledu zabezpieczenia to kod **nieuruchomiony ani razu, siedzacy w najbardziej krytycznym miejscu calej operacji**. **Dowod produkcyjny:** bramka na liczbie wierszy przy D-008 wywalila sie skladniowo, ZANIM cokolwiek sprawdzila - `psql` NIE podstawia zmiennych `:nazwa` wewnatrz bloku cytowanego dolarami (`DO $$ ... $$`), wiec `:oczekiwana` doleciala do serwera doslownie. Tym razem bylo GLOSNO (`ON_ERROR_STOP`, transakcja sie wycofala, zero szkody). Ale ten sam blad o wlos obok jest CALKOWICIE CICHY: `SELECT ... INTO oczek` z pustej tabeli daje NULL, a `IF n <> NULL` daje NULL, czyli NIE-prawde - `IF` sie nie wykonuje, wyjatku nie ma, **migracja przechodzi bez kontroli, a w logu stoi linia sugerujaca, ze bramka byla**. Porownanie z pustka jest grozniejsze niz brak porownania. **Why bad:** zabezpieczenie ZMIENIA DECYZJE (ryzykowna operacje odpalasz smielej, bo "jest bramka"), wiec falszywe jest gorsze niz jego brak - dokladnie jak kopia zapasowa, ktora twierdzi, ze istnieje (RUNBOOK punkt 1); sciezka sukcesu wykonuje sie zawsze, sciezka alarmu nigdy - az do dnia, w ktorym wszystko od niej zalezy; cisza strażnika jest nieodroznialna od poprawnosci (to samo co AP-310 i AP-306). **Correct:** (1) odpal zabezpieczenie ze ZLYM wsadem i ZOBACZ, jak zatrzymuje, zanim zaufasz mu przy dobrym - przy D-008 kosztowalo to jedno uruchomienie i trzy minuty przestoju; (2) bramka ma padac ZAMKNIETA, jawne `IF oczek IS NULL THEN RAISE EXCEPTION`, bo domyslne zachowanie SQL przy NULL to przepuszczenie; (3) w `psql` wartosc wpuszczaj osobnym zapytaniem (tabela tymczasowa, `SET`) i czytaj ja w bloku; (4) test sciezki ALARMU jest wart wiecej niz test sciezki sukcesu - kontrakt nazwy przy D-008 sprawdzono pieciema celowymi przywroceniami wady. Pelny opis: docs/anti-patterns/AP-314_bramka_ktorej_nikt_nie_widzial.md.

### AP-315: Walidator sprawdza FORME tekstu, a nie jego GATUNEK
**Ustanowiony 10/08/2026 (Manager AGS, po szesciu dniach zywej publikacji).** Rodzina AP-312 od strony TRESCI: tam nazwa stanu obiecuje co innego, niz znaczy; tu **tekst przechodzi wszystkie kontrole, bo kazda pyta o jego KSZTALT, a zadna o to, CZYM ON JEST**. Warstwa kontroli tresci rosnie zawsze w te sama strone - myslniki, zakazane slownictwo, dlugosc, interpunkcja, jezyk, meta-naglowki - i wszystko to sa pytania o FORME. Notatka recenzyjna modelu ma forme bez zarzutu, wiec przechodzi komplet. **Dowod produkcyjny:** material #344 zatwierdzony 03/08, opublikowany 04/08 o 16:01, zdjety recznie 10/08 - **szesc dni na profilu LinkedIn, 87 wyswietlen, pod nazwiskiem Tomasza** - a trescia posta bylo "I've reviewed the canonical text and Voice Bible. (...) strong content. However, I need to flag an issue before...", czyli CM mowiacy do operatora o materiale, razem z nazwa wewnetrznego artefaktu. **Cztery kontrole, kazda zadala wlasciwe pytanie i kazda przepuscila:** `strip_meta_header` pytal o KSZTALT naglowka (tekst byl proza, wiec zaden wzorzec go nie dotknal), `enforce` o myslniki, slownictwo i polszczyzne (wszystkie odpowiedzi poprawne), bramka HITL o to, **czy zatwierdzone** (bylo - tapniete odruchowo), raportowanie Managera o to, **czy kolejka jest pusta** (byla, bo material wyszedl). Piata warstwa: tresc wycieku stala w `stan_gry` rano 04/08, PRZED publikacja, w tej samej linii co status - sesja przeczytala STATUS, nie TRESC. **To projekt, nie wypadek** (sformulowanie Managera): o stan i o forme latwo zapytac, o gatunek trzeba zapytac swiadomie. **Why bad:** zielony przebieg walidatora wyglada identycznie niezaleznie od tego, czy sprawdzil wszystko, czy tylko to, o co potrafil zapytac; koszt jest publiczny i szesciu dni na profilu nie da sie cofnac; kazda nowa kontrola formy zwieksza poczucie bezpieczenstwa, nie zmniejszajac ryzyka gatunkowego ani o krok; bramka ludzka NIE jest tu zabezpieczeniem, bo zatwierdzanie odruchowe to normalny tryb pracy operatora zamykajacego kilkanascie kart tygodniowo (ta sama klasa co AP-314). **Correct:** kontrola GATUNKU osobno od kontroli formy, postawiona na OSTATNIEJ bramce przed swiatem (u nas w `worker.process_item` przed zapisem `handed_off` - tamtedy przechodzi takze material zatwierdzony guzikiem w n8n, z pominieciem cm-agenta); sprawdzaj DOKLADNIE ten tekst, ktory wyjdzie, czyli wiersz kolejki, nie `canonical_body` (publikuje sie wariant); bezpiecznik ZATRZYMUJE, nie poprawia - poprawiona notatka to nadal notatka; **podziel liste na TWARDA i MIEKKA wedlug jednego kryterium: czy slowo ma sensowne uzycie POZA nasza maszyneria** (`Voice Bible`, `masterprompt`, `stan_gry` nie maja; `kolejka`, `meldunek`, `canonical` maja, bo TNM pisze po polsku do uslug lokalnych, gdzie "kolejka klientow" i "stac w kolejce" sa naturalne - twarda blokada na zwyklym slowie odpali raz, w najgorszym momencie, i sam bezpiecznik stanie sie AP-312); furtke "drugie zatwierdzenie" wiaz z TRESCIA, nie z fraza (tekst przepisany jest nowym tekstem); meldunek o zatrzymaniu MUSI nazywac FRAZE, bo "cos jest nie tak" odtwarza ten sam odruch, ktory doprowadzil do wpadki; przy diagnozie czytaj TRESC, nie tylko status - status odpowiada na pytanie "gdzie to jest", nie "co to jest". **DRUGA TURA TEGO SAMEGO DNIA, przyczyna zrodlowa:** kilka godzin po wdrozeniu listy fraz przyszla karta z wariantem "Rozumiem Twoja prosbe, ale widze niejasnosc: nie podales mi tekstu do poprawy (...) otrzymasz zwrotnie wylacznie poprawiony tekst, zero em dashy, zero angielskich kalk" - czyli **doslownym echem promptu `compliance.polish_pl`**. Model nie poprawil tekstu, odpowiedzial O tekscie, a `_rewrite` oddawal to dalej przez `return out or text`, bez zadnego sprawdzenia. To kanal, ktorym niemal na pewno wyszla takze publikacja z 04/08; obsluguje TRZY filtry naraz. Funkcja miala starannie zrobiona obsluge przypadku, w ktorym filtr PADNIE (AP-306), i zadnej obslugi przypadku, w ktorym filtr ODPOWIE. **Lista fraz dala na tym tekscie `([], [])` - zero trafien**, bo to inna awaria tego samego rodzaju o zupelnie innym slownictwie. **Naprawa strukturalna zamiast dopisywania fraz:** mierz POKRYCIE SLOW wejscia w wyjsciu - przerobka zachowuje slowa oryginalu, rozmowa o przerobce ich nie ma. Ponizej progu 0.35 filtr oddaje tekst WEJSCIOWY nietkniety i zglasza do agent_logs z wlasnym typem. To kontrakt, nie heurystyka: kazdy z trzech promptow obiecuje zachowanie sensu i dlugosci. Zmierzone: rozmowa 0.023, korekta polszczyzny 0.977, ostre przepisanie 0.651, skrocenie o polowe 0.372. **Zasada ogolna warta wiecej niz sama poprawka: kazde wywolanie modelu, ktorego wynik wraca do potoku jako DANE, potrzebuje bramki wyjscia - bo "odpowiedz o zadaniu" i "wynik zadania" sa dla kodu nieodroznialne, oba sa napisem.** Pelny opis: docs/anti-patterns/AP-315_walidator_formy_nie_gatunku.md.

---

## How to add entries

When agents fail in production OR Tomasz catches an issue during HITL review:

1. Add new entry with next sequential AP-XXX number (AP-001 series for voice, AP-100 for content, AP-200 for strategic)
2. Date the entry
3. Reference the agent + session where it was caught
4. Update relevant agent's prompt to explicitly prevent this pattern
