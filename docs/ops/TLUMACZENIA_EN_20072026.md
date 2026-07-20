# KARTA KONTROLNA TLUMACZEN PL->EN (incydent publikacji 20/07)

Wykonanie SQL naprawczego = zatwierdzenie tlumaczen. Sens 1:1, glos AGS, zero em-dash.


## Wiersz 182 (x, slot 21 20:10)

**PL (zatwierdzone przez Ciebie):**
Cztery intencje działały bez problemów. Piąta odpowiada na pytanie o reklamację informacją o cenie. Żaden log nie sygnalizuje błędu. System wydaje się działać. Nie działa.

**EN (pojdzie na kanal):**
Four intents worked without a hitch. The fifth answers a complaint question with pricing info. No log flags an error. The system appears to work. It doesn't.


## Wiersz 183 (x, slot 21 21:57)

**PL (zatwierdzone przez Ciebie):**
Klasyfikator intencji z 90% skutecznością przy czterech kategoriach nie ma gwarancji, że utrzyma ten poziom przy pięciu. Granice między intencjami się zacierają. Model decyduje nie tylko „czy to pytanie o cenę", ale „czy to pytanie o cenę, czy coś, co brzmi podobnie, ale tym nie jest". Bez warstwy kierowania to zmiana granic decyzyjnych całego systemu, którą nikt jednak tak nie określa.

**EN (pojdzie na kanal):**
An intent classifier at 90% accuracy with four categories has no guarantee of holding that level with five. The boundaries between intents blur. The model no longer decides just "is this a pricing question" but "is this a pricing question, or something that sounds like one and isn't". Without a routing layer, that is a change to the decision boundaries of the whole system. Nobody calls it that, though.


## Wiersz 184 (x, slot 22 16:11)

**PL (zatwierdzone przez Ciebie):**
Warstwa kierowania to osobne miejsce: próg poniżej którego bot pyta zamiast zgadywać, powrót do opcji domyślnej, gdy nic nie pasuje, decyzja o tym, kto przejmuje kontrolę (człowiek czy moduł). To wymaga konkretnej pracy, zanim liczba intencji wzrośnie do punktu, w którym cicha awaria stanie się normą.

**EN (pojdzie na kanal):**
The routing layer is its own place: a threshold below which the bot asks instead of guessing, a fallback when nothing fits, a decision about who takes over (a human or a module). That takes concrete work, before the number of intents grows to the point where silent failure becomes the norm.


## Wiersz 185 (x, slot 22 17:55)

**PL (zatwierdzone przez Ciebie):**
Cztery intencje wybaczają brak architektury. Piąta już nie. Szósta pokaże to jeszcze wyraźniej. Dodanie kolejnej funkcji do bota to dobry moment, aby zapytać: czy system w ogóle wie, kiedy nie wie.

**EN (pojdzie na kanal):**
Four intents forgive missing architecture. The fifth doesn't. The sixth will make it even clearer. Adding another feature to a bot is a good moment to ask: does the system even know when it doesn't know.


## Wiersz 210 (x, slot 27 18:06)

**PL (zatwierdzone przez Ciebie):**
Sobota, popołudnie. Ktoś buduje agenta do klasyfikacji pięciuset zgłoszeń supportowych i wybiera najdroższy dostępny model. Uzasadnienie: "lepszy model to lepszy wynik". Dwa dni wcześniej ten sam ktoś użył tego samego modelu do jednego zdania podsumowania w raporcie. Oba wybory są błędne. Z różnych powodów.

**EN (pojdzie na kanal):**
Saturday afternoon. Someone builds an agent to classify five hundred support tickets and picks the most expensive model available. The reasoning: "better model, better result". Two days earlier the same person used the same model for a one-sentence summary in a report. Both choices are wrong. For different reasons.


## Wiersz 211 (x, slot 27 19:46)

**PL (zatwierdzone przez Ciebie):**
Koszt na zadanie to nie jest szczegół księgowy. To dane wejściowe do decyzji architektonicznej, taki sam jak opóźnienie czy dostępność. Odkładanie go na później ("zoptymalizujemy koszty później") to sygnał, że architektura powstała bez planu.

**EN (pojdzie na kanal):**
Cost per task is not an accounting detail. It's an input to an architectural decision, same as latency or availability. Postponing it ("we'll optimize costs later") is a signal the architecture was built without a plan.


## Wiersz 212 (x, slot 27 21:54)

**PL (zatwierdzone przez Ciebie):**
Klasyfikacja pięciuset zgłoszeń: wysoka częstotliwość, niski koszt błędu (ticket trafia do człowieka, który go poprawia). Tańszy model wystarczy. Podsumowanie kontraktu: niska częstotliwość, wysoki koszt błędu (reputacja, ryzyko prawne, czas na naprawę). Tu droższy model to inwestycja, nie wydatek.

**EN (pojdzie na kanal):**
Classifying five hundred tickets: high frequency, low cost of error (the ticket lands with a human who corrects it). A cheaper model is enough. Summarizing a contract: low frequency, high cost of error (reputation, legal risk, time to repair). There the pricier model is an investment, not an expense.


## Wiersz 213 (x, slot 28 14:06)

**PL (zatwierdzone przez Ciebie):**
Trzeba macierzy zadań. Oś X: częstotliwość. Oś Y: koszt błędu. Wysoka częstotliwość i niski koszt błędu dostaje tani model automatycznie. Niska częstotliwość i wysoki koszt błędu dostaje drogi model bez dyskusji. Rzeczywista architektura żyje pośrodku macierzy.

**EN (pojdzie na kanal):**
You need a task matrix. X axis: frequency. Y axis: cost of error. High frequency and low error cost gets the cheap model automatically. Low frequency and high error cost gets the expensive model, no debate. Real architecture lives in the middle of the matrix.


## Wiersz 214 (x, slot 28 16:13)

**PL (zatwierdzone przez Ciebie):**
Warunkowe kierowanie: tani model jako filtr, eskalacja do droższego gdy pewność spada poniżej progu albo gdy zadanie ma cechy wysokiego ryzyka (kwota transakcji, słowa z zakresu prawa, negatywny wydźwięk). To nie kompromis. To architektura, która inwestuje w jakość dokładnie tam, gdzie jakość się liczy.

**EN (pojdzie na kanal):**
Conditional routing: a cheap model as the filter, escalation to a pricier one when confidence drops below a threshold or when the task carries high-risk markers (transaction amount, legal wording, negative sentiment). That's not a compromise. That's architecture that invests in quality exactly where quality matters.


## Wiersz 215 (x, slot 28 17:47)

**PL (zatwierdzone przez Ciebie):**
Jeden model do wszystkiego wygląda na prostszą decyzję. Jest tylko droższa w skali i mniej dokładna tam, gdzie dokładność się liczy. Koszt na zadanie zasługuje na taką samą uwagę co wybór narzędzia czy schemat bazy danych.

**EN (pojdzie na kanal):**
One model for everything looks like the simpler decision. It's just more expensive at scale and less accurate where accuracy matters. Cost per task deserves the same attention as your choice of tools or your database schema.
