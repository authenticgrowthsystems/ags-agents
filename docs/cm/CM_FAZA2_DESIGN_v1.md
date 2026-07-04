# CM FAZA 2 - projekt: proaktywny planer + zarządzanie celami (04/07/2026)

**Fundament:** CM_BRAIN_DESIGN_v2 (Faza 2) + kanon 11a (toggle + kreator konfiguracji) + kanon 10 (work_mode).
**Status:** decyzje D-F2-1..4 u Tomasza (guziki); implementacja po odpowiedziach. Design przed kodem.

## 1. Proaktywny planer (CM sam przychodzi z planem)

```
TRIGGER (D-F2-1): cron (rozszerzenie CM Reports Cron o trzeci schedule) i/lub "zaplanuj tydzien" w rozmowie
  -> cm-agent /plan (endpoint istnieje) -> planner.py:
     wsad: brand_strategy (pillars/audience) + SCHOWEK (inspirations 'new') + content_memory (co gralo/czego
     nie dublowac) + kadencja per cel (channels.config.posts_per_week + sloty preferowane) + plan biezacy
     model: tier 'planner' (Opus 4.8, router R4, koszt do cm_tasks)
  -> INSERT content_items status='proposed' (temat + cel/e + scheduled_for per slot)
  -> JEDNA wiadomosc na Telegram: ponumerowana lista propozycji tygodnia
AKCEPTACJA W ROZMOWIE (model jednego approve, D2): "zatwierdz plan" / "wywal 3" / "zamien 5 na temat X" /
  "przesun 2 na czwartek" -> narzedzia plan_approve / plan_edit -> 'proposed' -> 'planned'
GENERACJA (D-F2-3): T-24h przed slotem (swiezosc + mozliwosc reakcji na biezace) albo od razu po akceptacji
  -> normalny pipeline: canonical -> warianty w jezyku celu -> JEDNO approve materialu -> publikacja w slocie
```
Zmiana w pętli: item 'planned' z przyszłym slotem czeka (claim gating jak dla 'approved'); generacja rusza
w oknie T-24h (albo natychmiast, wg D-F2-3).

## 2. Zarządzanie celami (toggle + kreator; wymóg kanonu 11a)

```
/agents -> nowy przycisk "⚙️ Cele" (+ komenda /cele) -> lista WSZYSTKICH celow z channels:
  ✅ AGS x (active) | ✅ AGS linkedin (active) | 🕐 AGS linkedin_page (ready) | 🕐 TNM linkedin (ready) | ...
  tap na cel -> karta celu: status, jezyk, kadencja, work_mode, stats_mode + guziki:
    [Wlacz/Wstrzymaj] tgl:<brand>:<channel>  [Konfiguruj] -> kreator w rozmowie CM
WLACZENIE celu 'ready': walidacja kompletnosci (tokeny pod secret_prefix w sejfie? org_urn gdy org_api?)
  -> brakuje = jasna lista brakow z instrukcja (per platforma - fundament pod instalator-kreator 11b)
  -> komplet = status 'active' + hook powitalny (propozycje adaptacji z archiwum - juz LIVE)
KREATOR KONFIGURACJI (rozmowa CM, narzedzia target_create/target_update):
  "dodaj cel: strona TNM na LinkedIn" -> CM proponuje konfiguracje SKOPIOWANA z najblizszego istniejacego
  celu ("bierzemy ustawienia jak AGS linkedin, jezyk zmieniam na polski?") -> zapis do channels.config
WORK_MODE per cel (kanon 10, D-F2-2):
  'supervised' (dzis): kazdy material przez Twoje approve
  'semi': plan zatwierdzasz HURTEM, materialy publikuja sie w slotach BEZ per-item approve (compliance gate zostaje)
  'auto': pelna mechaniczna kolejka wg algorytmu; Ty dostajesz tylko raporty
  Default: 'supervised'; zmiana per cel w karcie celu.
```

## 3. Zakres techniczny
- cm-agent: planner.py (nowy), narzedzia plan_approve/plan_edit/target_create/target_update w rozmowie,
  walidator kompletnosci celu, zmiana claim gating dla 'planned'.
- n8n: przycisk "⚙️ Cele" + rodzina callbackow tgl:/cel: w HITL (wzorzec agsel:, IF 2.2 per AP-301);
  trzeci schedule w CM Reports Cron (gdy D-F2-1 = cron).
- DDL: ZERO nowych tabel (plan zyje w content_items 'proposed'; konfiguracja w channels.config -
  standard kluczy: posts_per_week, slots[], work_mode, language_publish, stats_mode, secret_prefix, org_urn).
- **RLS przed aktywacja TNM/RDC** (kanon z Bramy 2): osobny krok przy pierwszym wlaczeniu celu 2. marki -
  policies per brand_id na tabelach contentowych; zaplanowany, nie w tym pakiecie kodu.

## 4. Decyzje ROZSTRZYGNIETE (Tomasz, guziki 04/07)
- **D-F2-1 trigger:** niedziela 20:15 (po raportach tygodniowych) + na zadanie ("zaplanuj tydzien").
- **D-F2-2 work_mode:** trzy tryby od razu (supervised/semi/auto), default supervised, przelaczane per cel.
- **D-F2-3 generacja: CALY PLAN OD RAZU po akceptacji** + CM uczy sie w locie: nowe inspiracje/sytuacje ->
  CM sam proponuje przesuniecia/dodatki BEZ lamania kolejki (kazda taka decyzja = AUTONOMOUS_DECISION + widoczna
  w rozmowie i raportach).
- **D-F2-3b STAN AWARYJNY (nowy wymog, "super wazne"):** material czeka na approve, slot nadchodzi, Tomasz
  MILCZY -> po **24h od wyslania approve** CM przechodzi w tryb awaryjny: wybiera najlepsza opcje i publikuje
  w slocie automatycznie. Kazda publikacja awaryjna: log AUTONOMOUS_DECISION + wyrazne powiadomienie na kanale
  logowym ("opublikowalem awaryjnie - brak reakcji 24h") + pozycja w raporcie dziennym. Wylaczalne per cel
  (config.emergency_publish, default ON per decyzja Tomasza).
- **D-F2-4 kadencja domyslna (per Tomasz, doslownie):** X = 3-5 postow DZIENNIE; LinkedIn = pon-pt post,
  sobota NIC, niedziela ARTYKUL (dokladnie ten rytm) + tresci spontaniczne poza planem.
  Zapis w channels.config: X {posts_per_day: [3,5]}, LinkedIn {weekly_pattern: {mon-fri: 'post', sat: null,
  sun: 'article'}}. Format 'article' = dluzsza forma (taxonomy/format per slot w planie).
- **D-F2-5 horyzonty planu:** szczegolowo TYDZIEN w przod; zarys MIESIACA generowany przy planie tygodnia
  (zapis: brand_config 'cm_month_outline', wersjonowany); KWARTAL/ROK = warstwa strategiczna Managera
  (Obsidian -> brand_strategy), planer ja czyta, nie tworzy.
- **Przypomnienie Tomasza (potwierdzone w mapie):** sledzenie reakcji na posty (kto skomentowal/zareagowal ->
  contacts + engagement_log) = warstwa CRM, kanon 9; mechanika zbierania per platforma wymaga docs-first
  researchu API -> pakiet CRM (Opiekun Relacji), nie Faza 2.

## 4b. KROK 2 Fazy 2 - zakres z feedbacku Tomasza po pierwszym planie E2E (04/07 15:31)
1. **Formatowanie planu (ZROBIONE w kroku 1b):** pelne tematy bez obcinania, grupowanie po dniach
   z naglowkami, emoji kanalow z rozroznieniem marki (🐦X / 💼LI-profil / 🏢LI-AGS / 💼LI-TNM...).
2. **NAWIGACJA ZATWIERDZANIA PLANU (guziki):** [✅ Zatwierdz wszystkie] jednym tapem ORAZ tryb
   przegladu jeden-po-drugim: karta pozycji (temat + slot + cele + STATUS: czeka/zatwierdzony/odrzucony/
   inny kat) z guzikami [✅] [❌] [🔄 inny kat] [⬅️ poprzedni] [➡️ nastepny]. Rodzina callbackow plannav:.
3. **Statusy pozycji widoczne** w liscie planu (nie tylko proposed - takze co juz zatwierdzone/odrzucone).
4. **Po przegladzie: automatyczna kolejka** (zatwierdzone pozycje ida w produkcje i sloty bez dodatkowych pytan).
5. **Inspiracje z Notion:** zapytanie do Managera wyslane (ZAPYTANIE_do_Managera_Notion_inspiracje_04072026.md);
   rekomendacja BE = jednorazowy ETL do inspirations (source='notion', dedup po notion_page_id), zero zywego
   odczytu Notion przez CM. ETL po odpowiedzi Managera (lista pul).
6. Egzekucja work_mode semi/auto (z kroku 1, przeniesione).

## 5. Acceptance (calosc Fazy 2)
(a) CM w niedziele (lub na zadanie) przysyla ponumerowany plan tygodnia zbudowany ze schowka+strategii+archiwum;
(b) "zatwierdz plan" -> pozycje 'planned' ze slotami; edycje w rozmowie dzialaja; (c) generacja odpala sie
wg decyzji D-F2-3 i konczy normalnym approve; (d) "⚙️ Cele" pokazuje wszystkie cele ze statusami; toggle
dziala; wlaczenie niekompletnego celu daje liste brakow; (e) kreator tworzy nowy cel kopiujac konfiguracje;
(f) work_mode 'semi' publikuje bez per-item approve po zatwierdzeniu planu (test na jednym celu).
