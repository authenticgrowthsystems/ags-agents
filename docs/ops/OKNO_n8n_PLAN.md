# OKNO n8n - plan całości (spinacz)

**Ten dokument USTALA KOLEJNOŚĆ i opisuje wyłącznie fazę rebuildu.** Szczegóły faz 2 i 3 leżą
w dokumentach, do których odsyła, i **nie są tu powtórzone celowo** - dwie instrukcje o tej samej
rzeczy starzeją się osobno (AP-316).

**Kod:** `72c52da`, `main` = `origin/main`, drzewo czyste, zestaw **38/38**.
**Na produkcji stoi:** `cm-agent:bc` - zawiera TYLKO bloki B i C. Bloki **G i E czekają**.

## CO DOMYKA TO OKNO

| faza | co | gdzie | dokument |
|---|---|---|---|
| 1 | rebuild: bloki **G** (D-015, D-022) i **E** (kod D-021) | serwer, docker | ten plik, niżej |
| 2 | rejestracja narzędzia **nowy prospekt** | n8n, `AGS Lacznik Chat Tools` | `docs/ops/D021_NARZEDZIE_N8N_NOWY_PROSPEKT.md` |
| 3 | **D-017**, token w 44 węzłach | n8n, `HITL Handler` | `docs/ops/OKNO_D017_przygotowane.md` |

**Dlaczego taka kolejność, a nie inna:**

1. **Rebuild pierwszy**, bo faza 2 rejestruje narzędzie wołające endpoint, który dopiero ten
   rebuild wystawia. Odwrotna kolejność dałaby narzędzie strzelające w nieistniejący adres,
   czyli AP-307 w miniaturze.
2. **D-017 na końcu, bo jest najbardziej ryzykowna.** Dotyka 44 węzłów **jedynego interfejsu
   Tomasza**. Gdy idzie ostatnia, wszystko przed nią jest już potwierdzone zachowaniem, więc
   po ewentualnej awarii wiadomo, co ją spowodowało. Sformułowanie z długu: **ryzykiem nie jest
   token, tylko skrypt na 44 węzłach.**
3. Fazy 2 i 3 dotykają **dwóch różnych workflow**, więc nie kolidują ze sobą.

**Token NIE jest rotowany w tym oknie** (decyzja Managera 19.08). Rotacja to osobny krok
po 24 godzinach stabilności.

**Po każdej fazie zatrzymujemy się na weryfikacji prawdziwą wiadomością.** Nie przechodzimy dalej,
dopóki poprzednia nie odpowie zachowaniem. Kod odpowiedzi HTTP nie jest dowodem - 19.08
`/health` zwracało `ok`, gdy każda ścieżka wołająca model była martwa (D-023).

---

# FAZA 1: rebuild z blokami G i E

## KROK 1.1 (Mikrus): pobierz kod i SPRAWDŹ, co przyszło

```bash
cd ~/ags-agents && git pull --ff-only && git log --oneline -3 && git branch --show-current
```

**Warunek przejścia dalej:** na górze stoi **`72c52da`**, a gałąź to **`main`**.

Jeśli gałąź jest inna, zatrzymaj się i wklej wynik. 19.08 serwer stał na gałęzi sesyjnej,
a `git pull` wyglądał na pełny sukces i przyniósł kod sprzed ośmiu dni. **Sam fakt, że pull się
udał, nie jest dowodem, że masz właściwy kod.**

## KROK 1.2 (Mikrus): zbuduj obraz, jeszcze bez przestoju

```bash
cd ~/ags-agents && docker tag cm-agent:bc cm-agent:prev-ge && cd cm-agent && docker build -t cm-agent:ge . && docker images | grep cm-agent
```

**Warunek:** `prev-ge` ma **ten sam identyfikator** co `bc`, a `ge` jest nowy.
Przy innym identyfikatorze `prev-ge` zatrzymaj się.

## KROK 1.3 (Mikrus): podnieś nowy obraz

```bash
cd ~/ags-agents/cm-agent && docker rm -f cm-agent; docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:ge && sleep 15 && curl -fsS http://localhost:8089/health; echo
```

## KROK 1.4: weryfikacja PRAWDZIWĄ WIADOMOŚCIĄ

Napisz do bota **`/karty`**.

- Jeśli **jest** karta materiału: sprawdź, czy godzina publikacji ma **pełną datę i godzinę**.
  Przy materiale bez wiersza w kolejce karta ma **wprost powiedzieć, że dokładnej godziny nie zna**
  (to jest poprawka D-015). Karta podająca samą równą godzinę bez tego zastrzeżenia znaczy,
  że stary obraz nadal chodzi.
- Jeśli **nie ma** kart: napisz **`zapamiętaj na zawsze: nie używaj słowa test`** - ma przyjść
  odmowa D-019, tak jak 19.08. To dowodzi, że kontener wstał, choć nie dotyka samego bloku G.

**Wklej odpowiedź.** Dopiero potem faza 2.

## RATUNEK fazy 1

```bash
cd ~/ags-agents/cm-agent && docker rm -f cm-agent; docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:prev-ge && sleep 15 && curl -fsS http://localhost:8089/health; echo
```

Uwaga na kolejność (RUNBOOK punkt 2): łańcuch `&&` chroni DANE, nie DOSTĘPNOŚĆ. Jeśli coś padnie
między `docker rm` a `docker run`, kontener zostaje wyłączony - wtedy wykonaj samo `docker run`.

---

# FAZA 2 i FAZA 3

Prowadzone z dokumentów wymienionych w tabeli na górze. **Nie zaczynamy fazy 2 przed
potwierdzeniem fazy 1 zachowaniem, ani fazy 3 przed potwierdzeniem fazy 2.**

## Po oknie

- protokół okna do `docs/ops/`, na wzór `PROTOKOL_OKNA_19082026.md`;
- zamknięcia D-017 i D-021 (część n8n) do `docs/ops/DLUG_TECHNICZNY.md`;
- rotacja tokenu jako **osobny krok po 24 godzinach stabilności**, też z weryfikacją prawdziwą
  wiadomością;
- następne w kolejce: **blok H** (D-024), potem **D-025**.
