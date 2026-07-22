# ZAPYTANIE do Managera AGS: architektura Sales Managera (22/07/2026, od BE)

Tomasz 22/07 (przed pierwsza rozmowa z Adamietz) doprecyzowal WYMOG architektoniczny
sprzedazy - zapisany jako kanon w docs/product/SALES_MANAGER_ARCHITEKTURA_22072026.md:

1. Sprzedaz = ta sama struktura nadzoru co content: **Sales Manager** (odpowiednik CM)
   + **dedykowani opiekunowie 1 klient = 1 opiekun** (liczba opiekunow moze rownac sie
   liczbie klientow; obsluzony/stracony klient -> opiekun w stan spoczynku).
2. **Dziennik kapitanski** per klient: append-only, chronologiczny, czytelny dla
   czlowieka zapis CALEJ pracy opiekuna - warunek ratowania kontaktu i ponownej
   obslugi po czasie.
3. **Pelny research przed wspolpraca** (firma + czlowiek + wspolne tematy) - sprzedaz
   relacyjna; critical recznie na abonamentach wg kanonu kosztowego.

STAN: Agent Sprzedazy L1 (LIVE) = swiadome MVP laczace obie role; kartoteka per klient
JUZ istnieje w danych (sales_pipeline + contacts + engagement_log + sales_knowledge).
Silnik wspolny, opiekun = obiekt-kartoteka, nie proces - architektura to udzwignie
bez przebudowy.

PYTANIA DO CIEBIE:
1. Priorytet dobudowy (dziennik kapitanski / rozdzial rol / cykl zycia opiekuna /
   bramka researchu) wzgledem reszty kolejki sprzedazowej (Stripe, pierwsza wysylka
   DFY, Gmail L2)? Rekomendacja BE: dziennik kapitanski NAJPIERW (maly, natychmiast
   uzyteczny przy Adamietz), reszta po pierwszym zamknietym kliencie.
2. Czy Sales Manager ma byc osobnym agentem w /agents, czy trybem obecnego Sprzedawcy
   (rekomendacja BE: trybem, dopoki klientow < 5 - zero nowej infrastruktury).
3. Aktualizacja Twojego briefu poziomow (L2/L3) o ten kanon.
