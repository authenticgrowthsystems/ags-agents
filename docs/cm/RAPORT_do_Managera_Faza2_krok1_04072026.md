# RAPORT FAZA 2 / krok 1 (pełny zakres kodu): planer + stan awaryjny + ⚙️ Cele - od BE do Managera AGS

**Data:** 04/07/2026. **Status: KOD GOTOWY (py_compile PASSED) + gałęzie n8n LIVE; działanie po DDL 009 + rebuild.**

## Co zbudowane (wg CM_FAZA2_DESIGN_v1, decyzje Tomasza rozstrzygnięte guzikami)
1. **`app/planner.py` - proaktywny planer:** wsad = brand_strategy + SCHOWEK + archiwum 14 dni (antydubel)
   + bieżąca kolejka (bez kolizji slotów) + kadencja kanoniczna 11d (X 3-5/dzień; LinkedIn pn-pt post,
   sob nic, ND ARTYKUŁ - format article w slocie niedzielnym, temat prefiksowany [ARTYKUL]); model tier
   'planner' (Opus, wymuszone narzędzie emit_plan, koszt w cm_tasks); wynik: content_items 'proposed'
   + zarys miesiąca do brand_config (cm_month_outline, wersjonowany) + JEDNA ponumerowana wiadomość.
2. **Akceptacja/edycje w rozmowie CM:** narzędzia plan_build ("zaplanuj tydzień"), plan_approve
   (całość, wyjątki numerami), plan_edit (usuń/zmień temat/przesuń slot); propozycja planu z numeracją
   widoczna w kontekście rozmowy. Po zatwierdzeniu generacja CAŁOŚCI od razu (D-F2-3).
3. **STAN AWARYJNY (kanon 11c):** hitl.send_approval stempluje approval_requested_at; pętla co ≤30s
   promuje needs_approval starsze niż 24h -> 'approved' (publikacja w slocie) + AUTONOMOUS_DECISION
   + głośne powiadomienie na kanale logowym. Wyłączalne per cel (config.emergency_publish=false).
4. **⚙️ Cele (kanon 11a) - LIVE w HITL (233 węzły):** przycisk w menu /agents + komenda /cele -> lista
   WSZYSTKICH celów (✅/⏸/🕐, język, work_mode) z guzikami tgl:<brand>:<channel>; toggle z WALIDACJĄ
   kompletności (token pod secret_prefix w sejfie; org_urn przy stats_mode=org_api) - brak = czytelna
   lista braków (fundament instalatora 11b); po włączeniu hook powitalny (adaptacje z archiwum) zadziała
   automatycznie. Nowy cel / zmiana konfiguracji = narzędzia target_create (kopiuje config wzorca)
   / target_update w rozmowie CM. IF-y 2.2 (AP-301), zero hardkodów tokena.
5. **Cron planu:** CM Reports Cron + trzeci schedule niedziela 20:15 Europe/Warsaw -> POST /plan
   (kwadrans po raportach tygodniowych - planer widzi świeże wnioski).
6. **DDL db/009_faza2.sql:** approval_requested_at + GRANT brand_config dla roli workera + seed kadencji
   kanonicznej w config istniejących celów.

## Acceptance (mapowanie na design §5) - E2E po deployu
(a) plan w niedzielę + na żądanie: KOD+CRON TAK; (b) zatwierdzenie/edycje w rozmowie: KOD TAK;
(c) generacja całości od razu + normalne approve: KOD TAK; (d) ⚙️ Cele lista+toggle+braki: LIVE;
(e) kreator kopiujący konfigurację: KOD TAK; (f) work_mode semi/auto: pole i konfiguracja TAK -
egzekucja trybu 'semi' (publikacja bez per-item approve) wchodzi krokiem 2 Fazy 2 (świadomie:
wymaga zmiany w _draft/dispatch, do osobnego przetestowania; 'supervised' + stan awaryjny pokrywają
dzisiejszą potrzebę).

## Uczciwe ograniczenia kroku 1
- work_mode 'semi'/'auto': konfigurowalne, egzekucja w kroku 2 (patrz wyżej).
- Format [ARTYKUL] = prefiks tematu (content_items nie ma kolumny format; kolumna = kandydat do db/010,
  decyzja przy kroku 2).
- target_create ustawia adapter LinkedIn (jedyny webhook adapter dziś); przy FB/IG dojdzie mapa adapterów.

**Next:** deploy (Tomasz: push + DDL 009 + rebuild) -> E2E: "zaplanuj tydzień" + tap-test ⚙️ Cele ->
krok 2: egzekucja work_mode semi/auto + ewentualna kolumna format.
