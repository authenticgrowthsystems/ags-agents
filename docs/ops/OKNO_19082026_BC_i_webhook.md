# OKNO SERWEROWE 19.08.2026 - rebuild B+C plus prostowanie dziewięciu wierszy `webhook`

**Decyzja Managera 19.08:** prostujemy wszystkie dziewięć wierszy na `draft`, w JEDNYM oknie
razem z rebuildem bloków B i C. Kanałów aktywnych (`AGS/x`, `AGS/linkedin`) nie dotykamy.

**Kod:** `1eb298b` (bloki B i C), zestaw testów 35/35.
**Obraz przed oknem:** `cm-agent:d018` (= `latest`). Cofnięcie o krok: `cm-agent:ap315d`.
**SQL okna:** `docs/ops/SQL_webhook_na_draft_19082026.sql`.

Kolejność jest celowa: obraz budujemy PRZED zatrzymaniem kontenera, żeby przestój trwał
sekundy zamiast minut, ale pisarza zatrzymujemy PRZED `UPDATE`, bo `cm-agent` jest jedynym
pisarzem do `channels.config` (RUNBOOK punkt 3).

---

## KROK 0 (Windows, PowerShell): wypchnij kod

```bash
cd C:\Claude-CoWork\AGS\ags-agents; git push origin main
```

## KROK 1 (Mikrus): pobierz kod

```bash
cd ~/ags-agents && git pull --ff-only && git log --oneline -3
```

Na górze musi stać commit zaczynający się od `1eb298b`. Jeśli nie stoi, zatrzymaj się.

## KROK 2 (Mikrus): kopia tabeli i WERYFIKACJA kopii

RUNBOOK punkt 1: kopia, która TWIERDZI, że istnieje, jest gorsza niż jej brak.

```bash
docker exec pg_n8n pg_dump -U n8n -d ags_crd -t channels > ~/kopia_channels_19082026.sql && grep -c "^INSERT INTO\|^COPY" ~/kopia_channels_19082026.sql && ls -lh ~/kopia_channels_19082026.sql
```

Plik ma mieć niezerowy rozmiar i zawierać dane. Jeśli licznik pokaże `0`, **zatrzymaj się**.

## KROK 3 (Mikrus): stan PRZED, do protokołu

```bash
docker exec -i pg_n8n psql -U n8n -d ags_crd -c "SELECT brand_id, channel, status, config->>'publish_mode' AS tryb FROM channels ORDER BY 1,2;"
```

**Wklej wynik do rozmowy.** Zapiszę go do protokołu okna, zanim ruszymy dalej.

## KROK 4 (Mikrus): zbuduj nowy obraz, jeszcze bez przestoju

```bash
cd ~/ags-agents && docker tag cm-agent:latest cm-agent:prev-bc && cd cm-agent && docker build -t cm-agent:bc . && docker images | grep cm-agent
```

Na liście muszą być: `latest`, `prev-bc` (ten sam identyfikator co `latest`) i `bc` (nowy).
Jeśli `prev-bc` ma inny identyfikator niż `latest`, **zatrzymaj się**.

## KROK 5 (Mikrus): zatrzymaj pisarza

```bash
docker stop cm-agent && docker ps -a | grep cm-agent
```

## KROK 6 (Mikrus): uruchom SQL z bramką

```bash
docker exec -i pg_n8n psql -U n8n -d ags_crd -v ON_ERROR_STOP=1 < ~/ags-agents/docs/ops/SQL_webhook_na_draft_19082026.sql
```

Masz zobaczyć `BRAMKA OK: 9 wierszy do poprawienia, zero aktywnych.`, potem `UPDATE 9`,
potem `KONTROLA OK: zero wierszy z trybem webhook.` **Każde `BRAMKA:` albo `KONTROLA:` bez
słowa `OK` znaczy, że transakcja się wycofała i nic nie zmieniono - wklej to do rozmowy.**

## KROK 7 (Mikrus): podnieś nowy obraz

```bash
cd ~/ags-agents/cm-agent && docker rm cm-agent && docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:bc && sleep 15 && curl -fsS http://localhost:8089/health; echo
```

## KROK 8: weryfikacja PRAWDZIWĄ WIADOMOŚCIĄ (wymóg 3 z Z-1)

`200` z `/health` nie dowodzi niczego. Napisz do bota na Telegramie:

1. **`/karty`** - ma odpowiedzieć normalnie. Sprawdza, że kontener chodzi na nowym obrazie
   i że nic się nie wysypało przy starcie.
2. **"zapamiętaj na zawsze: nie używaj słowa ekosystem"** - ma odmówić widocznie, powiedzieć,
   że reguła NIE weszła do stylu, i że odłożył ją na bok. **Jeśli odpowie "zapisane na stałe",
   nowy obraz się nie podniósł.**

**Wklej obie odpowiedzi bota do rozmowy.**

---

## RATUNEK

**Wycofanie obrazu** (dane zostają poprawione, wraca stary kod):

```bash
cd ~/ags-agents/cm-agent && docker rm -f cm-agent 2>/dev/null; docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:prev-bc && sleep 15 && curl -fsS http://localhost:8089/health; echo
```

**Wycofanie danych**: sekcja "SQL ODWROTNY" na końcu pliku SQL, zakomentowana celowo.
Odkomentować wolno **tylko** po cofnięciu decyzji przez Managera.

**Uwaga na kolejność (RUNBOOK punkt 2):** łańcuch `&&` chroni DANE, nie DOSTĘPNOŚĆ. Jeśli coś
padnie między `docker rm` a `docker run`, kontener zostaje wyłączony. Wtedy wykonaj samo
`docker run` z ratunku wyżej.
