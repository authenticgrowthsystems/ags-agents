# SYNTEZA: AI sales agent tools - spiac czy budowac? (20/07/2026)

Job Researchera: `551dc3e6-2b17-44d0-bb49-1b16a5392dff` | poziom: medium | koszt: **1.57 PLN**
| 15 claims, 84 evidence. Kontekst oceny: nasz Agent Sprzedazy = partner strategiczny + HITL
(kazdy outreach zatwierdza Tomasz), NIE mass-mailer.

## Mapa rynku (trend 2026, conf 0.5)

Trzy warstwy: (a) dane/enrichment - Clay, Apollo, Dropcontact; (b) wykonawcza mass-outreach -
Instantly, Lemlist, HeyReach, Salesforge, Woodpecker; (c) CRM/agentowa - Attio, Warmly,
Amplemarket. Zrodla: [theaiagentindex.com](https://theaiagentindex.com/resources/guides/best-ai-agents-for-cold-email),
[nrev.ai blog](https://www.nrev.ai/blog/ai-sales-tools), [lindy.ai blog](https://www.lindy.ai/blog/ai-sales-agent-cold-email-outreach-features).

## Narzedzia po kolei

| Narzedzie | Co robi | Cena 2026 | Werdykt pod nasz model |
|---|---|---|---|
| **Clay.com** | Enrichment/orkiestracja danych: waterfall 50+ providerow w jednym flow, AI research agents, webhooks/HTTP API; NIE jest senderem (conf 0.75) | od ~$149 (Starter) do ~$800/mies. + credits; ukryte koszty per-credit (conf 0.6; [clay.com/pricing](https://www.clay.com/pricing), [university.clay.com billing](https://university.clay.com/docs/plans-and-billing)) | Jedyny realny kandydat do SPIECIA (warstwa enrichment pod nasza orkiestracje), ale $149+/mies. przy zero klientach = NIE teraz |
| **Instantly.ai** | Mass cold email: wiele skrzynek, warmup, sekwencje, lekki CRM (conf 0.75) | Growth ~$37-97, wyzsze $358-1000+/mies. (conf 0.55; [instantly.ai/pricing](https://instantly.ai/pricing)) | **Sprzeczny z HITL z definicji** (conf 0.7) - odpada |
| **HeyReach** | Automatyzacja LinkedIn outreach, multi-account pod agencje, API (Clay/n8n/Make) (conf 0.7) | ~$79-99/mies. per sender (conf 0.55; [heyreach.io/pricing](https://www.heyreach.io/pricing)) | Zbudowany pod skale multi-konto; API teoretycznie uzywalne punktowo po ludzkiej akceptacji (conf 0.5), ale to platny executor czegos co zrobimy sami - odpada na start |
| **Attio** | CRM-first z warstwa AI (research agents, auto-enrichment), silne API (conf 0.45) | NIEPOTWIERDZONE w evidence (conf 0.25) - sprawdzic attio.com/pricing przy potrzebie | Mamy wlasny CRM w PG (contacts + engagement_log + sales_pipeline DDL 027) - odpada |
| **Apollo.io** | Baza kontaktow B2B + enrichment + sequencing + lekki CRM (conf 0.55) | ma tani/darmowy tier (cennik 2026 niepotwierdzony w evidence) | Najtanszy kandydat na enrichment PUNKTOWO, gdy ruszy wolumen prospektow |

Artefakt zrodlowy: linki "arxiv.org/abs/web:URL" w evidence to znany artefakt normalizacji
(pulapka z docs/komponenty/researcher.md) - wlasciwe URL-e po dwukropku.

## Kluczowy wniosek

**Zadne z narzedzi nie ma natywnego trybu "czlowiek zatwierdza kazda wiadomosc przed wysylka"**
(conf 0.4) - HITL trzeba budowac na wierzchu ich API tak czy inaczej. Czyli: kupujac Clay/HeyReach
placimy za skale, ktorej nie chcemy, a warstwe partnerska (research + draft + guziki) i tak
piszemy sami. Nasz Agent Sprzedazy (BE-SPRZEDAWCA, DDL 027) to dokladnie ta brakujaca warstwa.

## 4 opcje Researchera (skrot) + rekomendacja

1. Najszybsza: Clay API (enrichment) + wlasna wysylka Gmail/SMTP z HITL.
2. Najtansza: Apollo (tani tier) + wlasny send; Clay/HeyReach dopiero przy budzecie.
3. Najwyzsze upside: pelny stack Clay+HeyReach+Attio jako czyste API-warstwy - over-engineering na Stage 0-1.
4. Najwyzsza pewnosc: **zero API-commitmentow na starcie**; narzedzia najwyzej recznie, wlasny
   agent na wlasnych danych; decyzja o Clay po 4-6 tyg. realnego wzorca uzycia.

**Rekomendacja BE: opcja 4 z furtka 2 (Pareto).** Budujemy swoje (juz w toku), nic nie kupujemy.
Prospect research robi nasz Researcher (5 zrodel LIVE, ~1.3-1.7 PLN/job medium - taniej niz
credit Clay). Apollo darmowy tier do sprawdzenia dopiero przy pierwszych 20+ prospektach, jesli
reczny research zacznie boleć. Szczegol w REKOMENDACJE D3.
