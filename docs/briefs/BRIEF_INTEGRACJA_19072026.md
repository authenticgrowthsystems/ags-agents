# BRIEF BUILDU: INTEGRACJA rownoleglych buildow (19072026) - budowniczy: BE-INTEGRATOR

Wywolanie sesji (URUCHOM DOPIERO gdy wszystkie 4 galezie build/* maja STATUS DONE w briefach):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_INTEGRACJA_19072026.md zbuduj`

## 1. CO robisz (jedyna sesja z prawem do sb-work, deployu i masterpromptu)

1. Sprawdz STATUS w 4 briefach (kolektor/dedup/porzadki/czyta-swiat) - DONE z dowodami.
2. Merge do claude/silly-blackwell-dfc32d W KOLEJNOSCI (w worktree sb-work):
   `git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" merge build/kolektor-x`
   potem build/dedup, build/porzadki, build/czyta-swiat. Konflikty spodziewane w: worker.py
   (kolektor tick + dedup w _draft + swiat tick - ROZNE funkcje, skladaj oba kawalki),
   matreview.py (dedup ⚠️ w _card + porzadki w akcji 'no' - ROZNE miejsca), conversation.py
   (tylko porzadki). Po KAZDYM merge: py_compile WSZYSTKICH zmienionych modulow.
3. Deploy JEDNA PACZKA: push (Tomasz) -> SSH: pull, psql db/025 (od kolektora), rebuild
   cm-agent, /health (szablony: masterprompt sekcja 8; sleep 15).
4. Tap-testy wszystkich 4 buildow wg DoD z ich briefow (sonda kolektora z cena Owned Read
   PRZED wlaczeniem crona!).
5. Zamkniecie za wszystkich: masterprompt (sekcja 4b -> STATUS integracji, next DDL),
   SCHEMA (jesli 025 dotknal), SYSTEM_DATAFLOW (kolektor + czyta-swiat), raport zbiorczy
   docs/cm/RAPORT_do_Managera_<data>_integracja.md, pamiec trwala (project_resume_point),
   sprzatanie worktree: `git -C "C:\Claude-CoWork\AGS\ags-agents" worktree remove <sciezka>`
   dla 4 buildowych (galezie zostaja w historii po merge).

## 2. Czego NIE robisz

Zadnych nowych feature'ow. Konflikt nie do zlozenia mechanicznie = STOP i pytanie do Tomasza
guzikami (ktora wersja), nie tworczosc wlasna.

## 3. Kolejnosc uruchomienia calego trybu (dla Tomasza)

4 okna rownolegle (kazde: Fable 5 na 2 prompty -> przelaczenie na Opus 4.8 konczy):
1) @docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_KOLEKTOR_METRYK_X_19072026.md zbuduj
2) @docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_BRAMKA_DUPLIKACJI_19072026.md zbuduj
3) @docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_PORZADKI_DETERMINISTYCZNE_19072026.md zbuduj
4) @docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_CM_CZYTA_SWIAT_19072026.md zbuduj
Po 4x DONE -> piate okno: ten brief (integracja + jeden deploy + tap-testy).

STATUS = READY (19/07 ~22:50, tryb rownolegly)
