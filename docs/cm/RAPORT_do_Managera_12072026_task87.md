# RAPORT do Managera - 12/07/2026: Task #87 execution_mode 3-poziomowy + agent_learning_log

Od: BUILD ENGINEER | Status: kod + DDL 020 GOTOWE, czeka SSH + rebuild. Zbudowane w dniu briefu.

## Wykonane (DDL + SCHEMA jeden commit, regula 08/07)

1. **db/020**: channels.execution_mode (supervised/semi_autonomous/autonomous, default supervised,
   CHECK idempotentny) + tabela agent_learning_log + indeks. **KOREKTA do briefu (AP-304):**
   content_item_id = UUID (content_items.id to UUID, dowod: 9f341eca), nie BIGINT z briefu.
2. **Zbieranie korekt (wszystkie sciezki decyzji)**: matreview.log_learning() wolane przy:
   karta Zatwierdz/Odrzuc (accepted/rejected), Zatwierdz WSZYSTKIE (accepted per pozycja),
   edycja tekstu-matki apply_edit (edited, old->new), edycja wariantu w rozmowie subagenta
   _apply_sub_edit (edited, per '<brand>:<channel>'), replace_material (replaced).
   Nigdy nie wywraca produkcji (try/except; przed DDL = cichy pass).
3. **Konsumpcja petli**: generate._learning_digest(brand) - ostatnie 20 decyzji (liczniki per
   typ + finalne wersje Tomasza jako wzorzec + odrzucone jako antywzorzec) dokladane do
   KAZDEJ generacji (canonical + warianty). Dziala obok istniejacych poziomow nauki
   (style_learned z destylacji edycji + zasady konta).
4. Pilot = wszystkie kanaly od razu (subagent X z briefu wlacznie) - logowanie jest wspolne,
   wiec zawezenie do pilota byloby sztuczne.

## Zakres NA POZNIEJ (świadomie)

- Egzekwowanie trybow semi_autonomous/autonomous (progi 'proste vs skomplikowane' per subagent,
  auto-approve) = po #86 (menu marek) i decyzjach Tomasza o progach. Dzis wszyscy supervised =
  zachowanie bez zmian.
- diff (kolumna) = rezerwa; destylacja roznic robi juz _distill_style_rules (VOICE_EDIT).

## Tap-test (po SSH 020 + rebuild)

1. Karta -> Zatwierdz/Odrzuc -> SELECT z agent_learning_log pokazuje wpis (dowod BE zrobi sweepem).
2. Po 2-3 decyzjach: nastepna generacja ma w prompcie OWNER DECISION HISTORY (dowod: jakosc/logi).
