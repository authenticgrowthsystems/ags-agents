# SYNTEZA: Payment processing PL/USD - co uruchomic DZIS (20/07/2026)

Job Researchera: `175abc14-59b6-4e33-9b5e-6758e824ad81` | poziom: medium | koszt: **1.10 PLN**
| 14 claims, 75 evidence | najwyzszy confidence z calej czworki (0.6).

## Fakty (docs-first, z linkami)

- **Stripe**: Payment Links + Invoicing bez kodu, PLN i USD z JEDNEGO konta (conf 0.8).
  Rejestracja polskiej DG online ([dashboard.stripe.com/register](https://dashboard.stripe.com/register)):
  NIP, dane rejestrowe, konto bankowe PLN, dane reprezentanta; KYC automatyczne - konto
  przyjmuje platnosci zwykle od razu, dokumenty moga byc dociagane przed WYPLATA (conf 0.75;
  [wise.com/pl/blog/stripe-polska](https://wise.com/pl/blog/stripe-polska)). Payment Link
  mozliwy dzis/jutro (conf 0.65). **Przelewy24/BLIK dziala JAKO METODA WEWNATRZ Stripe**
  dla PLN (conf 0.65; [docs.stripe.com/payments/p24](https://docs.stripe.com/payments/p24)).
  Prowizje: ~1.5% + 0.25 karty EU, ~2.9% + oplata karty spoza EU - dokladny cennik PL
  DO POTWIERDZENIA w panelu (conf 0.5, conflict_flag).
- **GHL Payments/Invoices**: to NIE jest procesor platnosci - wymaga podpietego Stripe/PayPal/
  NMI jako backendu (conf 0.7; [help.gohighlevel.com payments](https://help.gohighlevel.com/support/solutions/155000000067)).
  Faktury z linkiem platniczym, one-time i subskrypcje - ale nie przyspiesza PIERWSZEJ
  platnosci, bo Stripe i tak trzeba zalozyc (conf 0.65).
- **Przelewy24 solo**: PLN/BLIK, rejestracja z NIP + weryfikacja dokumentow + oplata
  aktywacyjna (zwracana), aktywacja kilka dni roboczych - NIE natychmiast (conf 0.7;
  [registration.przelewy24.pl](https://registration.przelewy24.pl/)). Slaba obsluga USD.
- **PayU**: PLN, ograniczona natywna obsluga USD (conf 0.5).
- **Paddle / Lemon Squeezy (Merchant of Record)**: przejmuja VAT/sales tax za sprzedaz
  zagraniczna, ale prowizja ~5% + oplata (conf 0.7); Lemon Squeezy po przejeciu ogranicza
  nowych merchantow = ryzyko (conf 0.4). Airwallex: wzmianka bez potwierdzen (conf 0.3).

## 4 opcje Researchera

1. **Najszybsza (rank 1): Stripe dzis** - Payment Link PLN + drugi w USD z jednego konta.
2. Najtansza: Stripe + P24 jako metoda (unika 5% MoR).
3. Najwyzsze upside: Stripe jako backend + GHL Invoices (CRM-spojnosc, ale wolniejszy start).
4. Najwyzsza pewnosc: MoR dla USD + P24/PayU dla PLN (drogo, dwa systemy).

## REKOMENDACJA BE: opcja 1+2 polaczone (Stripe, DZIS)

Kroki dla Tomasza (jedyna czesc wymagajaca czlowieka - konto zaklada wlasciciel, nie agent):

1. Wejdz na https://dashboard.stripe.com/register i zaloz konto na dane DG (NIP, konto PLN).
2. W Dashboard: Settings -> Payment methods -> wlacz **Przelewy24 + BLIK** (klient PL placi
   przelewem/BLIK-iem, nie tylko karta).
3. Utworz 2 Payment Links: "AGS - System retencji klientow - setup" w PLN i drugi w USD
   (kwoty wg decyzji D1 z REKOMENDACJE). Payment Links -> New.
4. Test: przelej 10 PLN wlasna karta, sprawdz webhook/mail potwierdzenia, zrob refund.
5. (Pozniej, nie blokuje) podpiac Stripe pod GHL Invoices, gdy ruszy delivery DFY.

VAT/ksiegowosc dla USD spoza UE: temat dla ksiegowej Tomasza (eksport uslug, zwykle NP
z adnotacja reverse charge) - poza zakresem researchu, JAWNIE nierozstrzygniete.
