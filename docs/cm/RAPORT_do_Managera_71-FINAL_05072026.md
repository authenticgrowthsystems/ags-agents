# RAPORT KONCOWY do Managera - TASK #71 Notion -> PostgreSQL SSOT

**Od:** BUILD ENGINEER (BE)
**Data:** 05/07/2026 wieczor
**Status:** WSZYSTKIE FAZY A-F WYKONANE + CUTOVER DONE. Formalne CLOSED po 24h monitoringu
(kontrola 06/07 wieczor: drift cron 03:00 bez alertu + kolejka sync czysta).
**Terminy:** kontrakt zakladal cutover 08/07 i zamkniecie 09/07 - wykonane **05/07, 3-4 dni
przed terminem**. Raporty czastkowe z dowodami: docs/cm/RAPORT_do_Managera_71-{A,B,C,D,E,F}_*.md.

---

## 1. LICZBY ZBIORCZE (wszystko zweryfikowane na produkcji)

| Faza | Co weszlo | Kluczowe liczby |
|---|---|---|
| A (04/07) | mapping APPROVED 10/10 + DDL 010 + sample | 17 nowych tabel, kotwice notion_page_id/entry_hash |
| B (05/07) | doktryna kompletna + agenci | Blueprint/BE Contract/Cross-Posting/ICP/Sales Bible, Story Bank 20+bio, 6 masterpromptow, 2 kontrakty, silnik 12/12 |
| C (05/07) | zywe dane | task_queue 14, manager_daily_log 130, content_items 8, contacts 45 (zero dubli), chat_registry 8, inspirations 18, pricing Lokalna 3 |
| D (05/07) | K6+K7 | 24 wpisy: vendor_registry 8, pricing ags_premium 7 (ROZJAZD cennika ROZWIAZANY doktryna Multi-Layer + decyzja Tomasza guzikami), funnel, sales_page, 3 playbooki, sekwencja ABM, 3 ghl_config |
| E (05/07) | K8-10 | 81 wpisow: roadmap 16, raporty subagentow 12 (9 daily + 3 weekly), monthly merge 1, **decyzje Managera 49**, validated_patterns, gate build_input, weekly_plan; DDL 013 |
| F (05/07) | sync + cutover | DDL 014+015, worker LIVE w cm-agent, testy A/B/C sekcji 8 ZALICZONE, **67/67 stron READ-ONLY MIRROR fail=0**, drift cron 03:00 |

**Razem: ~350 wpisow zmigrowanych do 17 nowych tabel + rozszerzenia 5 istniejacych;
3 pg_dumpy przed fazami (528K/585K/59xK); 0 utraconych danych.**

## 2. SYNC DB->NOTION (mechanizm sprzedawalny)
Wg trzech decyzji Managera z 05/07: worker w cm-agent (watchdog, LISTEN+poll, SKIP LOCKED,
backoff->Telegram), hybryda re_render/append wg mapy 23 tabel w sync_registry (dolaczenie tabeli
= UPDATE, zero rebuildu), v1 enabled = brand_config + manager_daily_log. Docs-first rozstrzygniecie:
Notion BEZ bulk delete -> **soft-clear z trackingiem** (nowa sekcja na gorze <10s niezaleznie od
rozmiaru strony; id-y blokow w sync_mirror_state; stara sekcja archiwizowana w tle).
Testy z produkcji: re_render 2s, append 2s, podmiana sekcji +100 zarchiwizowanych, drift wykrywa
reczne edycje (md5 callouta 1:1) + alert na bocie #2. Flaga brand_config.sync_to_notion per marka
= klient bez Notion nie placi kosztu (Zasada 3).

## 3. INCYDENTY -> LEKCJE (wszystkie naprawione tego samego wieczora)
1. **AP-305 (NOWY, x2):** Notion 404 = brak Connection integracji do drzewa stron, nie zle ID
   (Nawrocki Hub przy D, drzewo TNM przy E). Connections dodane - drzewa AGS+Nawrocki+TNM pokryte.
2. **AP-304 recydywa:** 1. wersja DDL 013 pominela 'critical_escalation' (researcher db/007) -
   czytac WSZYSTKIE DDL-e tabeli, nie pierwszy grep. Dowod z pg_get_constraintdef naprawil w 1 iteracji.
3. **Test C zlapal 2 realne dziury** (czlowiek > skrypt): kontrola callouta przepuszczala dopiski
   (fix: md5 calego tekstu, DDL 015) + alert nie wychodzil z one-shot kontenera (fix: token z
   app_secrets ladowany w drift_check).

## 4. POZA #71: PAKIET UX CM (feedback Tomasza 05/07, WDROZONY tego samego wieczora)
Spec: docs/cm/CM_UX_FEEDBACK_05072026.md; modul cm-agent/app/matreview.py + galaz n8n mat* (239 wezlow).
- intake materialu = guziki [Do kolejki]/[Dzis]/[Odrzuc] (matdec:);
- przeglad materialow = KARTY ⬅️➡️ z 4 decyzjami, w tym **"✅⏭ Zatwierdz na koniec kolejki"**
  + ostrzezenie SLOT MINAL (koniec floodu: od 2 materialow jedna zbiorcza wiadomosc);
- niedziela: przypomnienia co 15 min (21:30-23:00), o 23:00 CM sam zatwierdza material
  z PRZYSZLYM slotem (albo przypina pn 10:00) + alert bot #2 - kanon 11c nietkniety.
Tap-test Tomasza na zywo: paczka 45 materialow przegladana kartami ("jest pieknie").

## 5. DO ZAMKNIECIA / NASTEPNE
- [ ] 06/07: kontrola 24h (drift.log po cronie 03:00 + Telegram bez alertow) -> **#71 CLOSED**.
- [ ] Przeglad reszty paczki materialow przez Tomasza (fallbacki czuwaja: niedzielny 23:00 + 11c 24h).
- [ ] Master prompt build-in-public o #71 juz w CM (dedup 0.24, material w obrobce).
- Nastepne watki wg mapy: iteracyjne dolaczanie tabel do sync_registry (1/dzien, kolejnosc
  Managera), CM Faza 2 reszta (work_mode semi/auto, kolumna format), i18n, RLS przed 2. marka.
