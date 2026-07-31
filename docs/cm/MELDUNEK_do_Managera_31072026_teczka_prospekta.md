# MELDUNEK: para zapisz_tekst + teczka gotowa (31/07/2026)

**Od:** BE (Budowniczy Systemów) → **Do:** Manager AGS
**Stan:** kod gotowy, commit `24b58a6`, test 36/36 PASS, zestaw 18/18 PASS.
**Produkcja: jeszcze nietknięta.** Czeka na cztery kroki Tomasza (na końcu).

---

## 1. Ustalenie, które zmieniło kontrakt

Zanim cokolwiek napisałem, sprawdziłem odczytem, czy `contact_id` ma na co wskazywać.
Nie miał.

| rejestr | wierszy | z mailem | z `contact_id` |
|---|---|---|---|
| `contacts` | 194 | **0** | - |
| `sales_pipeline` | 133 | - | **0** |

Pokrycie po nazwie: **1 na 133**.

`contacts` to uchwyty z X i LinkedIna zbierane przez radar komentarzy (`jasonfeifer`,
`mieszkojaroniewski`). `sales_pipeline` to prospekty kampanii - szkoły tańca. **To są dwie
rozłączne populacje.** Szkoła tańca, do której piszesz mail, nie ma w `contacts` ani jednego
wiersza i nigdy nie miała.

Gdybym wziął kontrakt dosłownie i oparł `contact_id` o `contacts`, narzędzie byłoby martwe
dokładnie dla tego, po co powstało.

**Co zrobiłem zamiast tego:** identyfikator jest rozstrzygany wobec **obu** rejestrów - UUID
albo fragment nazwy - i teczka zawsze mówi, w którym trafiła (`lejek` albo `kontakt`).
**Czego nie zrobiłem:** nie założyłem 133 wierszy w `contacts` pod prospekty. To zrobiłoby
drugie źródło prawdy o tym samym podmiocie, a kanon z 22/07 mówi wprost, że źródłem prawdy
o prospekcie jest lejek.

## 2. Cztery decyzje, które podjąłem sam - do Twojej wiadomości

1. **`status='draft'` to nowa wartość, nie recykling `proposed`.** `proposed` jest konsumowane
   przez strażnika gotowców Sprzedawcy. Gdybym zapisywał tam szkice, **każdy mail pisany
   w Cowork rodziłby po dobie bramkę „Outreach czeka na wysłanie"**. Test tego pilnuje.
2. **Dołożyłem piąty kanał: `whatsapp`.** Podałeś `email | sms | dm | telefon`, ale kanon
   zimnej wysyłki z 27/07 mówi „WhatsApp, nie SMS". Bez tej wartości wiadomość wysłana
   faktycznym kanałem kampanii musiałaby być zapisana kłamliwie jako SMS.
3. **`zapisz_tekst` przyjmuje opcjonalny `next_step` z terminem.** Wymagałeś, żeby `teczka`
   zwracała „ostatni ustalony next step z datą" - a **nic w systemie takiego kroku nie
   ustalało**. `sales_pipeline` miał samą datę bez zdania, a `contacts.next_action` istnieje
   od DDL 001 i **nie zapisał go nigdy nikt** (0 wierszy). Dołożyłem `sales_pipeline.next_step`
   i wpisałem ustalanie kroku w tę samą ścieżkę, co zapis tekstu: kto wysyła, ten wie, co dalej.
   Cztery parametry z Twojego kontraktu działają bez zmian, reszta jest opcjonalna.
4. **`dm` celuje w LinkedIn**, bo to kanał DM kampanii. Gdy dojdą DM-y na X, dokładamy klucz -
   nie zgaduję po treści.

## 3. Czego narzędzie NIE zrobi

- **Nie założy kontaktu po cichu.** Nieznany identyfikator wraca błędem z listą podobnych
  (szukanie po każdym słowie osobno) i zdaniem „NIC nie zapisałem".
- **Nie zgadnie przy wieloznaczności.** „Egurrola" trafia w trzy franczyzy - rozstrzyga pełna
  nazwa albo UUID. Ta sama rodzina wad, co dedup po samej domenie przy imporcie.
- **Nie ukryje pustki.** Brak następnego kroku jest wypisany słowami, nie zostawiony pustą
  linią - to była jedna z przyczyn diagnozy z 26/07.

## 4. Test, którego wymagałeś

Trzy wpisy dla jednego kontaktu → `teczka` zwraca je **w kolejności** i z poprawnym następnym
krokiem. Plus historia sprzed migracji (wpis Sprzedawcy wiszący na samej nazwie) jest widoczna
i stoi chronologicznie **przed** nowymi. 36 asercji, wszystkie zielone. Cały zestaw: 18/18.

## 5. Znalezione przy okazji

**Skrypt tworzący workflow Łącznika losował NOWY sekret przy każdym uruchomieniu.** Sekret siedzi
w ścieżce triggera MCP, więc **dołożenie jednego narzędzia zerwałoby Ci adres konektora
claude.ai** i rozjechało go z `app_secrets`. Naprawione: skrypt przejmuje sekret z żywego
workflow, nowy generuje tylko gdy workflow nie istnieje.

**Dług D-009:** gotowiec mailowy Sprzedawcy ląduje w kanale `Other`, a tekst z teczki w `Email`.
Nie poprawiłem od ręki, bo ta wartość jest kluczem dopasowania przy unieważnianiu starych
gotowców - podmiana bez migracji istniejących wierszy odtworzyłaby wadę StandART z 24/07.
Nic nie psuje dziś (teczka łączy po kluczu), ale liczenie wysyłki per kanał będzie kłamać.

**Dług D-003 zamknięty w połowie:** jest już ludzka droga zapisu treści i następnego kroku.
Pól kontaktowych przy wierszu lejka nadal nie da się wypełnić ręcznie, więc dojście przez
Piotra dalej nie ma swojego miejsca.

## 6. Co czeka na Tomasza - w tej kolejności

Kolejność nie jest dowolna: narzędzia MCP wołają endpointy, których jeszcze nie ma, a endpointy
potrzebują kolumn z DDL 036.

1. push gałęzi `claude/silly-blackwell-dfc32d`
2. SSH: kopia bazy
3. SSH: `git pull` + DDL 036 + rebuild cm-agent
4. Windows: PUT workflow n8n (dokłada dwa narzędzia, adres konektora bez zmian)

Po kroku 4: **restart rozmowy z konektorem**, żeby czat zobaczył nowe narzędzia, i tap-test -
zapisz jeden mail przy prospekcie z kampanii, potem poproś o teczkę.

**Czekam na następne zadanie.** Walidacja długości i pole formatu stoją nietknięte, kolejka X
pusta - nie ruszałem.
