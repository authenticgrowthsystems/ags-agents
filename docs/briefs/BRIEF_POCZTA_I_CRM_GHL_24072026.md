# BRIEF: poczta + CRM (GoHighLevel) dla Agenta Sprzedazy

**Zgloszenie Tomasza 24/07:** "docelowo musimy miec skonfigurowana poczte a najlepiej CRM -
GoHighLevel - po co wywarzac otwarte drzwi?"

Status: **BACKLOG, nie wchodzi bez decyzji o kolejnosci.** Brief istnieje, zeby pomysl nie
utonal w czacie i zeby nastepna sesja nie zaczynala od zera.

## Dlaczego to ma sens

GHL jest juz w naszym rejestrze narzedzi - to jest ten "system retencji", ktory sprzedajemy
klientom (vendor_registry + ghl_config z migracji #71: subaccount AGS, izolacja TNM przez
location_id). Sprzedajemy narzedzie, ktorego sami nie uzywamy do wlasnej sprzedazy. To
niekonsekwencja, a przy okazji: kazdy dzien wlasnego uzycia to material do build-in-public
i dowod, ze system dziala.

## Co dzis boli (dowody z sesji 24/07)

- Gotowiec przychodzi na Telegram, a wysylka jest reczna z prywatnej skrzynki: brak historii
  watku, brak informacji czy mail dotarl i czy zostal otwarty.
- `sales_pipeline.notes` to jedyna os czasu klienta. Dziala, ale nie wie nic o mailach.
- Dane kontaktowe wyciagamy regexem z notatek i claims (`_kontakt_prospekta`), bo nie ma
  jednego miejsca, gdzie mieszka mail i telefon decydenta.
- Follow-up jest reczny: `outreach_sent` ustawia +3 dni, ale nikt nie pilnuje wysylki.

## Zakres L1 (najmniejsza wersja, ktora cos zmienia)

1. **Kontakt w GHL = zrodlo prawdy o danych kontaktowych.** Prospekt z lejka zaklada/aktualizuje
   kontakt (imie, nazwisko, mail, telefon, tagi: zrodlo, branza, etap). `sales_pipeline` trzyma
   `ghl_contact_id`, naglowek gotowca czyta dane STAMTAD zamiast z regexa.
2. **Wysylka mailem przez GHL** zamiast recznego kopiowania: gotowiec dalej zatwierdza Tomasz
   (HITL, kanon: NIC nie wysyla sie samo), ale jednym tapnieciem, a nie przeklejaniem.
3. **Zwrotka do lejka:** dostarczenie/otwarcie/odpowiedz -> wpis w notatkach + zmiana etapu.

## Pytania do rozstrzygniecia PRZED kodem (docs-first)

- Ktory adres nadawczy: prywatny Tomasza czy hello@ na domenie AGS (reputacja domeny,
  SPF/DKIM/DMARC - wysylka zimna z niezweryfikowanej domeny to droga do spamu).
- API GHL: ktory endpoint kontaktow i konwersacji, limity, sposob uwierzytelnienia
  (token do app_secrets - kanon sekretow), czy subaccount AGS ma potrzebne uprawnienia.
- Czy zimny outreach ma w ogole isc przez GHL, czy tylko dalszy ciag relacji (ryzyko
  reputacyjne subaccountu, ktory obsluguje takze klientow).

## Kanony, ktore obowiazuja

- **NARZEDZIA NIE UJAWNIAMY:** nazwa GHL nigdy nie pada w komunikacji z prospektem.
  Wewnetrznie uzywamy, na zewnatrz sprzedajemy REZULTAT.
- **HITL:** nic nie wychodzi bez zatwierdzenia Tomasza, takze po podpieciu poczty.
- **Warstwy:** GHL to KANAL (interfejs/transport), nie mozg. Zrodlem prawdy o lejku zostaje
  baza `ags_crd`; GHL nie moze stac sie druga, konkurencyjna prawda o kliencie.
