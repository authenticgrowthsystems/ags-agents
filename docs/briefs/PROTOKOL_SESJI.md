# PROTOKOL SESJI BUDOWLANYCH (kanon 19/07/2026, decyzja Tomasza)

Kazdy osobny build (agent, subagent, kolektor, adapter) = OSOBNE okno kontekstowe,
spojne z kregoslupem architektury. Zero dodatkowych promptow od Tomasza poza wywolaniem.

1. KREGOSLUP = docs/RESUME_MASTERPROMPT_<najnowszy>.md (+ SCHEMA, DATAFLOW, anti-patterns,
   pamiec trwala). Aktualizuje go SESJA KONCZACA, nie Tomasz.
2. BRIEF = docs/briefs/BRIEF_<nazwa>_<data>.md wg _TEMPLATE_BRIEF.md. Pisze go sesja
   planujaca (Manager/BE) na polecenie Tomasza; Tomasz tylko akceptuje.
3. WYWOLANIE: jedna linijka z dwoma @plikami. Sesja czyta OBA zanim dotknie czegokolwiek.
4. ROWNOLEGLOSC: domyslnie sesje SEKWENCYJNIE na sb-work. Rownolegle buildy = osobna galaz
   od sb-work per build + sesja integracyjna (merge); NIGDY dwie sesje na tej samej galezi.
5. ZAMKNIECIE (obowiazkowe, sekcja 6 briefu): raport + masterprompt + pamiec + status briefu.
   Sesja, ktora tego nie zrobi, zostawia nastepcy zgadywanie - to byl blad handoffu 19/07.
