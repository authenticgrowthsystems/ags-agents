# RAPORT do Managera - 12/07/2026: Task #89 long-form delivery + karta approved

Od: BUILD ENGINEER | Status: **KOD GOTOWY (commit 0dda670), czeka rebuild cm-agent**
Zakres: Fix Priority 1 (karta approved) + Fix Priority 2 (plik dla long-form) - OBA przed
terminami (13/07 i 14/07). Fix Priority 3 (panel web + input plikiem) = nie ruszony, wg planu.

## Root cause 4 symptomow z 12/07 (diagnoza z kodu, nie z hipotezy)

1-2. Uciete artykuly CM ("mowi to...", "and only then r"): **max_tokens odpowiedzi rozmowy
   CM = 1200 (subagent 900)** - artykul 6000+ znakow fizycznie nie mial prawa wyjsc calo.
   Do tego hitl.send_approval przycina wiadomosc do [:3800] (limit Telegrama).
3. Input >4096 od Tomasza: limit Telegrama po stronie klienta (Fix P3, nie ruszany dzis).
4. Karta nie otwiera sie dla approved: pending_items() = TYLKO status='needs_approval'.

## Fix (0dda670, zero DDL)

- **Karta podgladu approved/dispatching/published**: show_review_cards z theme_fragment
  najpierw szuka w przegladzie, potem w zatwierdzonych - karta view-only (🔒 status, bez
  guzikow decyzji) z guzikiem **"📄 Pokaz pelna tresc (do skopiowania)"**.
- **matnav:fulltext**: pelna tresc dowolnego materialu KAWALKAMI po ~3900 znakow (ciecie
  na granicy akapitu) + dla [ARTYKUL] i tresci >3900 dodatkowo **plik .md** (sendDocument
  multipart, helper _tg_send_document wzorowany na _tg_upload_photo).
- **hitl.send_approval**: kazdy wariant >3500 znakow leci dodatkowo jako plik .md z podpisem
  "PELNA tresc (wiadomosc wyzej jest ucieta)".
- **max_tokens rozmowy: CM 1200->4000, subagent 900->2000** (koszt tylko przy realnym uzyciu).

## Tap-test (po rebuildzie, ~2 min)

1. Do CM: "pokaz mi tresc artykulu TNM" (albo inny zatwierdzony/opublikowany temat) ->
   karta 🔒 z guzikiem 📄 -> tap -> pelna tresc kawalkami + plik .md.
2. Nastepny material long-form w przegladzie -> pod wiadomoscia approval plik .md z pelna trescia.

## Zostaje w #89 (wg briefu, terminy pozniejsze)

Fix P3: panel web localhost:8089/panel + input plikiem od Tomasza (srednioterminowo).
