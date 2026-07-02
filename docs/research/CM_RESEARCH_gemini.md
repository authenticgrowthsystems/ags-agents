# **Architektura wieloagentowego systemu konwersacyjnego opartego na Telegram Bot API i Python FastAPI**

Wdrożenie skalowalnej architektury dla sieci agentów AI (multi-agent) sterowanej za pomocą jednego bota Telegram wymaga precyzyjnego podziału odpowiedzialności pomiędzy warstwą interfejsu użytkownika (UI) a warstwą logiczną. Przejście z monolitycznego systemu opartego na narzędziu n8n, w którym dotychczasowy przepływ składał się z 206 węzłów, na dedykowane mikroserwisy w języku Python, eliminuje ograniczenia wydajnościowe oraz ułatwia wersjonowanie i utrzymanie kodu. Projektowany system ma charakter modułowy, co oznacza, że każdy agent funkcjonuje jako autonomiczny serwis, a klient ma możliwość dokupywania dostępu do kolejnych agentów, którzy natychmiastowo pojawiają się jako nowe pozycje w tym samym boczku konwersacyjnym.

## **1\. Przełączanie kontekstu agentów w jednym bocie**

Sprawne zarządzanie wieloma agentami w jednym oknie czatu nakłada konieczność zaprojektowania intuicyjnego interfejsu, który przejdzie pomyślnie test łatwości użycia dla osób nietechnicznych, jednocześnie zachowując pełną kontrolę nad stanem sesji w bazie danych PostgreSQL.

### **Narzędzia Telegram Bot API w sterowaniu kontekstem**

Telegram udostępnia zestaw natywnych komponentów interfejsu, których odpowiednia kombinacja pozwala na bezwysiłkowe przełączanie kontekstów:

* **Menu poleceń (setMyCommands)**: Tradycyjne, globalne komendy są niewystarczające w systemie modułowym. Bot API pozwala jednak na dynamiczne nadawanie uprawnień i definiowanie komend dla konkretnych użytkowników za pomocą metody setMyCommands z parametrem scope ustawionym na BotCommandScopeChat(chat\_id=...)1. W momencie wykrycia zakupu nowego agenta, system wysyła żądanie do API, natychmiastowo aktualizując menu szybkiego wyboru w lewym dolnym rogu ekranu danego klienta1.  
* **Klawiatury stałe (ReplyKeyboardMarkup)**: Jest to najprostsze narzędzie z punktu widzenia niedoświadczonego użytkownika. Duże, kafelkowe przyciski u dołu ekranu z opcjami resize\_keyboard=True oraz selective=True zapobiegają przypadkowemu wpisaniu błędnych komend tekstowych3. Kliknięcie przycisku głównego (np. „Wybierz Agenta”) wywołuje dynamiczne menu.  
* **Klawiatury osadzone (InlineKeyboardMarkup)**: Wykorzystujące parametr callback\_data przyciski powiązane bezpośrednio z dymkiem wiadomości. Pozwalają one na natychmiastową, bezgłośną komunikację z serwerem bez zaśmiecania historii rozmowy wiadomościami tekstowymi użytkownika.  
* **Głębokie linkowanie (deep-linking)**: Linki typu t.me/nazwa\_bota?start=payload są kluczowe w procesie pozyskiwania i aktywacji modułów3. Po zakupie nowego agenta w panelu webowym klient otrzymuje spersonalizowany odnośnik. Jego kliknięcie automatycznie uruchamia bota, przesyła parametr autoryzacyjny i odblokowuje moduł w bazie danych bez jakiejkolwiek interakcji manualnej ze strony użytkownika3.

### **Model stanów konwersacji w PostgreSQL**

Architektura bota musi być całkowicie bezstanowa na poziomie serwera aplikacyjnego. Stan konwersacji każdego użytkownika jest odczytywany przy każdym przychodzącym żądaniu (webhooku) z tabeli stanów w bazie PostgreSQL5.

| Tabela bazy danych | Kluczowe kolumny | Rola w systemie |
| :---- | :---- | :---- |
| **user\_sessions** | chat\_id (PK), active\_agent\_id (FK), fsm\_state, context\_data (JSONB) | Przechowuje aktualnie aktywnego agenta dla danego czatu oraz bieżący krok w maszynie stanów (FSM)3. |
| **agent\_registry** | agent\_id (PK), display\_name, webhook\_url, is\_active | Centralny rejestr wszystkich dostępnych w systemie modułów agentowych wraz z adresami ich mikroserwisów. |
| **user\_subscriptions** | user\_id (PK), agent\_id (PK), granted\_at | Odpowiada za weryfikację uprawnień; determinuje, jakie pozycje zostaną wyświetlone użytkownikowi w menu wyboru. |

### **Analiza wzorców UX pod kątem użytkownika nietechnicznego**

W celu zapewnienia bezproblemowej obsługi bota przez osoby o niskich kompetencjach cyfrowych, porównano trzy główne podejścia interfejsowe:

| Parametr porównawczy | Komendy tekstowe (np. /seo, /copywriter) | Dynamiczne Menu Reply (Klawiatura dolna) | Menu Inline pod wiadomością startową |
| :---- | :---- | :---- | :---- |
| **Intuicyjność ("Test Mamy")** | Niska (wymaga pamiętania komend i poprawnej pisowni). | Bardzo wysoka (duże, czytelne przyciski tekstowe na dole ekranu)3. | Średnia (guziki znikają po przewinięciu historii rozmowy w górę). |
| **Odporność na błędy** | Niska (błędny zapis blokuje przetwarzanie lub wywołuje błąd). | Wysoka (użytkownik klika wyłącznie w zdefiniowane opcje). | Średnia (ryzyko kliknięcia w przycisk z nieaktualnego dymka). |
| **Narzut na API Telegrama** | Brak dodatkowych żądań optymalizacyjnych. | Średni (wymaga wysłania struktury klawiatury przy zmianie kontekstu)3. | Wysoki (wymaga ciągłego generowania nowych dymków z klawiaturami). |
| **Szybkość nawigacji** | Wolna (wymaga wywołania klawiatury znaków specjalnych). | Natychmiastowa (dostępna na stałe pod polem tekstowym). | Szybka (dostępna bezpośrednio w ostatniej wiadomości). |

**Rekomendacja UX**: Najbardziej niezawodnym wzorcem dla użytkownika nietechnicznego jest użycie **Reply Keyboard jako stałego punktu kontrolnego**. Klawiatura ta posiada stały przycisk „🤖 Zmień Agenta”. Jego kliknięcie powoduje wysłanie przez bot wiadomości z **Inline Keyboard**, która dynamicznie generuje listę kafli reprezentujących wyłącznie zakupione przez użytkownika moduły (na podstawie odczytu z tabeli user\_subscriptions). Kliknięcie wybranego agenta aktualizuje rekord active\_agent\_id w tabeli user\_sessions, czyści stan FSM oraz wysyła powitanie inicjujące od wybranego agenta (np. „Cześć, jestem Twoim Agentem SEO. Podaj adres URL do analizy”). Dzięki temu użytkownik nigdy nie pozostaje bez wizualnych wskazówek, jak sterować aplikacją.

## **2\. Architektura dwubotowa: interaktywny vs logowy**

W komercyjnych wdrożeniach systemów automatyzacji AI kluczowe jest oddzielenie ruchu konwersacyjnego od powiadomień systemowych i operacyjnych (np. raporty, potwierdzenia publikacji postów). Zapobiega to zakłócaniu interakcji z użytkownikiem oraz chroni system przed przekroczeniem limitów wydajnościowych API.

### **Porównanie rozwiązań: Dwa osobne boty vs Kanał z podziałem na tematy**

Poniższa tabela przedstawia szczegółowe porównanie techniczne dwóch głównych podejść do realizacji logowania i powiadomień:

| Kryterium porównawcze | Opcja 1: Dedykowany Bot B do logów i raportów | Opcja 2: Prywatny Kanał z włączonymi tematami (Topics) |
| :---- | :---- | :---- |
| **Doświadczenie użytkownika (UX)** | Powiadomienia trafiają do osobnego okna czatu. Pełna separacja wątków rozmowy od powiadomień systemowych. | Wszystkie logi lądują w jednym kanale podzielonym na tematy (np. osobny wątek per agent lub per klient)7. |
| **Limity API (sendMessage)** | Każdy bot posiada niezależną pulę limitów (30 wiadomości/s globalnie)8. | Obowiązuje limit 20 wiadomości na minutę do tej samej grupy/kanału8. |
| **Zarządzanie dostępem** | Trudne: każdy klient musi ręcznie wyszukać bota B i wysłać mu /start w celu rejestracji chat\_id w bazie. | Bardzo proste: administrator generuje jednorazowy link zapraszający do prywatnego kanału dla klienta. |
| **Ryzyko zablokowania bota (429)** | Niskie: ewentualna blokada bota B za spam nie wpływa na działanie interaktywnego bota A10. | Wysokie: przekroczenie limitu 20 wiadomości na minutę blokuje możliwość wysyłania powiadomień8. |
| **Złożoność wdrożenia** | Średnia: wymaga rejestracji u BotFather, przechowywania osobnego tokenu i obsługi nowego webhooka5. | Skrajnie niska: wystarczy jedno wywołanie API wysyłające log bezpośrednio na stałe ID kanału z określonym message\_thread\_id. |

### **Wpływ limitów Telegram API na architekturę powiadomień**

Telegram Bot API nakłada sztywne ograniczenia na liczbę wysyłanych komunikatów. Ich przekroczenie skutkuje błędem HTTP 429 i całkowitym zablokowaniem bota na czas określony w parametrze retry\_after10.

* **Wiadomości w czacie 1:1**: Maksymalnie 1 wiadomość na sekundę8. Krótkie skoki są tolerowane, ale ciągły ruch powyżej tej wartości generuje błędy8.  
* **Wiadomości do grup i kanałów**: Maksymalnie 20 wiadomości na minutę8.  
* **Globalny limit bota**: Maksymalnie 30 wiadomości na sekundę do wszystkich użytkowników łącznie8.  
* **Płatne transmisje**: Od wersji API 7.1 istnieje możliwość wysyłki do 1000 wiadomości na sekundę za opłatą 0.1 Telegram Stars za wiadomość (allow\_paid\_broadcast), jednak wymaga to zgromadzenia znacznego salda i dużej liczby aktywnych użytkowników, co wyklucza to rozwiązanie na etapie uruchamiania działalności8.

Jeżeli system wieloagentowy publikuje treści automatycznie i jednocześnie generuje logi z każdego etapu pracy (np. "Pobieranie źródeł", "Generowanie szkicu", "Analiza SEO") w tym samym oknie konwersacyjnym, w którym rozmawia użytkownik, natychmiastowo zostanie przekroczony limit 1 wiadomości na sekundę8. Doprowadzi to do zablokowania bota interaktywnego10. Dodatkowo, w celu uniknięcia nieskończonych pętli konwersacji między botami, Telegram całkowicie blokuje widoczność wiadomości wysyłanych przez inne boty, co wymusza odpowiednie projektowanie integracji8.  
**Rekomendacja architektoniczna**: Dla solo-przedsiębiorcy najbardziej optymalnym kosztowo i wdrożeniowo rozwiązaniem jest **Opcja 2 (Prywatny Kanał z włączonymi tematami \- Topics)**. Pozwala ono klientowi na pełne wyciszenie kanału powiadomień, aby nie rozpraszały go podczas interaktywnej rozmowy z botem A, a jednocześnie programista unika konieczności konfigurowania, zabezpieczania i opłacania infrastruktury pod drugiego bota.

## **3\. Routing wiadomości do agentów i asynchroniczny transport**

Zaprojektowanie wydajnego systemu modułowego wymaga całkowitego odejścia od przetwarzania synchronicznego. Ponieważ agenci AI mogą przetwarzać zapytania przez kilkadziesiąt sekund, trzymanie otwartego połączenia HTTP (webhooka) z serwerem Telegrama doprowadzi do timeoutów, które Telegram interpretuje jako awarię i zaczyna lawinowo ponawiać wysyłkę tego samego pakietu5.

### **Architektura przepływu i mechanizm Webhooka**

System wykorzystuje n8n wyłącznie jako lekki komponent proxy (transport webhooków). Zadaniem n8n jest odebranie żądania z Telegrama, natychmiastowe przekazanie go do routera FastAPI za pomocą metody HTTP POST i zakończenie połączenia statusem HTTP 200 OK w czasie poniżej 1 sekundy.

1. **Autoryzacja za pomocą Secret Token**: Router FastAPI weryfikuje nagłówek X-Telegram-Bot-Api-Secret-Token pod kątem zgodności z tokenem ustawionym podczas konfiguracji bota metodą setWebhook4. Zapobiega to próbom podszywania się pod serwery Telegrama przez podmioty trzecie17.  
2. **Deduplikacja aktualizacji**: Każde przychodzące żądanie posiada unikalny parametr update\_id4. Router sprawdza w bazie PostgreSQL, czy dany update\_id znajduje się w tabeli transakcyjnej. Jeśli tak, żądanie jest ignorowane jako duplikat sieciowy5.  
3. **Kolejkowanie asynchroniczne**: Router pobiera przypisanie agenta z tabeli user\_sessions, po czym zapisuje zadanie w tabeli agent\_jobs ze statusem PENDING i zwraca status HTTP 2006.  
4. **Przetwarzanie przez Workery**: Każdy agent uruchomiony jest jako osobny, niezależny proces worker w Pythonie. Worker odpytuje bazę danych o nowe zadania dla swojego agent\_id za pomocą zapytania blokującego wiersze, co zapobiega dublowaniu zadań przez wiele instancji tego samego agenta:

SQL  
UPDATE agent\_jobs   
SET status \= 'RUNNING', started\_at \= NOW()   
WHERE id \= (  
    SELECT id FROM agent\_jobs   
    WHERE agent\_id \= 'seo\_agent' AND status \= 'PENDING'   
    ORDER BY created\_at ASC   
    LIMIT 1   
    FOR UPDATE SKIP LOCKED  
)   
RETURNING \*;

### **Obsługa długich odpowiedzi i limitu 4096 znaków**

Wysyłanie ostatecznej odpowiedzi przez agenta za pomocą metody sendMessage musi uwzględniać limit 4096 znaków20. Ponieważ dane wyjściowe z LLM są sformatowane w MarkdownV2 lub HTML, proste pocięcie tekstu na równe części (np. po 4000 znaków) uszkodzi strukturę znaczników (np. pozostawi otwarty tag pogrubienia \* lub bloku kodu \`\`\`), co spowoduje odrzucenie wiadomości przez serwer Telegrama z błędem parsowania23.  
W celu poprawnego podziału wiadomości należy:

* Zmierzyć długość tekstu w **jednostkach kodu UTF-16**, ponieważ tak mierzy odchylenia (offsets) i długości encji Telegram Bot API25.  
* Użyć parsera AST (np. za pomocą biblioteki telegramify-markdown), który analizuje strukturę dokumentu Markdown i dzieli go na poziomie bezpiecznych granic bloków (paragrafy, listy, wiersze tabeli), domykając tagi wewnątrz każdego pojedynczego dymka wiadomości przed wysyłką25.

### **Implementacja routera FastAPI i integracji z cyklem życia aplikacji**

Poniższy kod przedstawia produkcyjną implementację routera FastAPI, który integruje się z asynchroniczną pętlą zdarzeń, weryfikuje bezpieczeństwo webhooka, deduplikuje żądania bezpośrednio w bazie danych i przekazuje zadania do kolejki PostgreSQL.

Python  
import os  
import logging  
import asyncio  
from contextlib import asynccontextmanager  
from fastapi import FastAPI, Request, Response, Header, HTTPException, status, Depends  
from pydantic import BaseModel, Field  
from typing import Optional  
import psycopg2  
from psycopg2.extras import RealDictCursor

\# Definicje zmiennych środowiskowych i połączeń  
DATABASE\_URL \= os.getenv("DATABASE\_URL", "postgresql://postgres:postgres@localhost:5432/agent\_db")  
TELEGRAM\_SECRET\_TOKEN \= os.getenv("TELEGRAM\_SECRET\_TOKEN", "super-secret-token-123")

logging.basicConfig(level=logging.INFO)  
logger \= logging.getLogger(\_\_name\_\_)

\# Pula połączeń PostgreSQL dla FastAPI  
def get\_db\_connection():  
    conn \= psycopg2.connect(DATABASE\_URL, cursor\_factory=RealDictCursor)  
    try:  
        yield conn  
    finally:  
        conn.close()

\# Inicjalizacja cyklu życia aplikacji (Lifespan)  
@asynccontextmanager  
async def lifespan(app: FastAPI):  
    logger.info("Inicjalizacja routera i weryfikacja bazy danych...")  
    \# Tutaj można umieścić asynchroniczne sprawdzanie połączeń z bazą danych  
    yield  
    logger.info("Zamykanie zasobów aplikacji...")

app \= FastAPI(lifespan=lifespan)

\# Modele danych Pydantic do walidacji struktur Telegram Bot API  
class TelegramUser(BaseModel):  
    id: int  
    is\_bot: bool  
    first\_name: str  
    username: Optional\[str\] \= None

class TelegramChat(BaseModel):  
    id: int  
    type: str

class TelegramMessage(BaseModel):  
    message\_id: int  
    from\_user: Optional\[TelegramUser\] \= Field(None, alias="from")  
    chat: TelegramChat  
    text: Optional\[str\] \= None

class TelegramUpdate(BaseModel):  
    update\_id: int  
    message: Optional\[TelegramMessage\] \= None

def process\_and\_route\_update(conn, update: TelegramUpdate) \-\> bool:  
    """  
    Weryfikuje unikalność aktualizacji (deduplikacja) i zapisuje zadanie w bazie danych.  
    """  
    if not update.message or not update.message.text:  
        return False

    chat\_id \= update.message.chat.id  
    update\_id \= update.update\_id  
    text\_payload \= update.message.text  
    user\_id \= update.message.from\_user.id if update.message.from\_user else chat\_id

    with conn.cursor() as cur:  
        try:  
            \# Próba wstawienia ID aktualizacji w celu detekcji duplikatów  
            cur.execute(  
                """  
                INSERT INTO processed\_updates (update\_id, chat\_id, processed\_at)  
                VALUES (%s, %s, CURRENT\_TIMESTAMP)  
                ON CONFLICT (update\_id) DO NOTHING;  
                """,  
                (update\_id, chat\_id)  
            )  
            \# Jeśli rowcount \== 0, oznacza to, że rekord o tym update\_id już istnieje  
            if cur.rowcount \== 0:  
                logger.warning(f"Zablokowano duplikat update\_id: {update\_id}")  
                return False

            \# Pobranie aktywnego agenta przypisanego do danej sesji czatu  
            cur.execute(  
                "SELECT active\_agent\_id FROM user\_sessions WHERE chat\_id \= %s;",  
                (chat\_id,)  
            )  
            session \= cur.fetchone()

            if not session:  
                \# Tworzenie domyślnej sesji w przypadku nowej konwersacji  
                cur.execute(  
                    """  
                    INSERT INTO user\_sessions (chat\_id, user\_id, active\_agent\_id, fsm\_state)  
                    VALUES (%s, %s, 'default\_general\_agent', 'IDLE');  
                    """,  
                    (chat\_id, user\_id)  
                )  
                active\_agent \= 'default\_general\_agent'  
            else:  
                active\_agent \= session\['active\_agent\_id'\] or 'default\_general\_agent'

            \# Dodanie zadania do kolejki PostgreSQL w celu asynchronicznego przetworzenia przez właściwy serwis agenta  
            cur.execute(  
                """  
                INSERT INTO agent\_jobs (chat\_id, user\_id, agent\_id, payload, status, created\_at)  
                VALUES (%s, %s, %s, %s, 'PENDING', CURRENT\_TIMESTAMP);  
                """,  
                (chat\_id, user\_id, active\_agent, text\_payload)  
            )  
            conn.commit()  
            return True  
        except Exception as e:  
            conn.rollback()  
            logger.error(f"Krytyczny błąd bazy danych podczas routingu: {str(e)}")  
            return False

@app.post("/webhook/telegram", status\_code=status.HTTP\_200\_OK)  
async def handle\_telegram\_webhook(  
    update: TelegramUpdate,  
    x\_telegram\_bot\_api\_secret\_token: Optional\[str\] \= Header(None),  
    db=Depends(get\_db\_connection)  
):  
    \# Weryfikacja nagłówka zabezpieczającego  
    if not x\_telegram\_bot\_api\_secret\_token or x\_telegram\_bot\_api\_secret\_token \!= TELEGRAM\_SECRET\_TOKEN:  
        logger.warning("Nieautoryzowana próba połączenia z webhookiem (błędny token)\!")  
        raise HTTPException(  
            status\_code=status.HTTP\_403\_FORBIDDEN,  
            detail="Forbidden: Invalid Secret Token"  
        )

    \# Procesowanie i routing wiadomości  
    if update.message and update.message.text:  
        is\_queued \= process\_and\_route\_update(db, update)  
        if not is\_queued:  
            return Response(content="Update ignored or already processed", status\_code=status.HTTP\_200\_OK)

    \# Zwrócenie pustej odpowiedzi 200 OK do Telegrama w celu zwolnienia webhooka  
    return Response(content="OK", status\_code=status.HTTP\_200\_OK)

## **4\. Konwersacyjny mechanizm Human-in-the-Loop (HITL)**

W komercyjnych systemach generowania treści (np. boty do automatyzacji social media) kluczowym elementem jest pętla zatwierdzania treści przez człowieka. Użytkownik nie powinien być ograniczony wyłącznie do sztywnych przycisków typu „Tak/Nie” – system musi wspierać naturalną konwersację (np. użytkownik pisze: „Popraw drugi akapit, dodaj więcej emocji”).

### **Wzorzec łączenia interakcji: ForceReply i reply\_to\_message**

Dla poprawnego powiązania komentarza użytkownika z konkretnym szkicem postu wygenerowanym przez AI, architektura wykorzystuje natywne powiązania wiadomości:

1. **Generowanie i wysłanie propozycji**: Agent AI tworzy treść postu i zapisuje ją w bazie PostgreSQL w tabeli content\_drafts z unikalnym identyfikatorem. Bot wysyła tę propozycję do użytkownika jako pojedynczą wiadomość wraz z przypisanym przyciskiem inline „Koryguj tekstowo”. ID wysłanej wiadomości (message\_id\_A) jest natychmiast mapowane w bazie danych z identyfikatorem szkicu27.  
2. **Aktywacja trybu edycji**: Gdy użytkownik klika „Koryguj tekstowo”, serwer odbiera żądanie CallbackQuery i wysyła nową wiadomość pomocniczą: „Wpisz swoje uwagi do powyższego szkicu:”, załączając obiekt ForceReply(selective=True)3. Wymusza to na aplikacji klienckiej Telegrama automatyczne zaznaczenie wiadomości bota i otwarcie trybu odpowiedzi (Reply)27.  
3. **Powiązanie i routing zwrotny**: Gdy użytkownik wysyła swoją uwagę, przychodzący obiekt Update zawiera pole message.reply\_to\_message22. Router odczytuje reply\_to\_message.message\_id, co pozwala na natychmiastowe zidentyfikowanie powiązanego szkicu w bazie danych29. Następuje pobranie pierwotnego tekstu i przekazanie go wraz z nowymi uwagami użytkownika z powrotem do agenta AI w celu wprowadzenia poprawek.

### **Maszyna stanów (FSM) i procedury wyjścia awaryjnego**

Wprowadzenie sesji w stan oczekiwania na decyzję (WAITING\_FOR\_REVISION) blokuje domyślne przetwarzanie innych komend przez tego samego agenta3. Aby zapobiec sytuacjom, w których użytkownik przypadkowo blokuje bota, projektuje się precyzyjne ścieżki wyjścia:

* **Przerwanie przez słowa kluczowe**: Przed przekazaniem tekstu do silnika FSM, router sprawdza, czy wiadomość użytkownika nie pasuje do wzorca anulowania (np. słowo anuluj, wyjdź lub komenda /cancel)3. W przypadku dopasowania, stan sesji w user\_sessions jest resetowany do IDLE, a użytkownik otrzymuje komunikat o pomyślnym anulowaniu trybu edycji3.  
* **Automatyczne wygasanie sesji (TTL)**: Proces tła (cron / worker powiadomień) regularnie sprawdza rekordy o statusie oczekiwania na korektę. Jeśli czas bezczynności użytkownika przekroczy określony czas (np. 30 minut), sesja jest automatycznie resetowana do stanu podstawowego, a klawiatura inline przy oryginalnym szkicu zostaje zaktualizowana (lub usunięta za pomocą editMessageReplyMarkup), aby zapobiec późniejszym kliknięciom w nieaktualne przyciski.

## **5\. Biblioteki i wzorce open-source**

Wybór odpowiednich bibliotek determinuje elastyczność i skalowalność kodu przy dalszym rozwoju produktu przez solo-przedsiębiorcę.

### **Porównanie frameworków pod kątem architektury asynchronicznej**

| Parametr techniczny | aiogram 3.x | python-telegram-bot (PTB) v21+ | Czysty klient HTTP (httpx \+ Pydantic) |
| :---- | :---- | :---- | :---- |
| **Architektura bazowa** | Całkowicie asynchroniczna, natywnie zaprojektowana pod programowanie reaktywne (asyncio)30. | Tradycyjna, zorientowana obiektowo, dostosowana do async w ostatnich wersjach31. | Brak frameworka; bezpośrednie wywołania asynchroniczne HTTP31. |
| **Zarządzanie stanami (FSM)** | Wysoce rozbudowany, wbudowany silnik FSM z łatwym bindowaniem do pamięci lub Redis30. | Posiada ConversationHandler, lecz jest on trudniejszy do integracji w środowisku rozproszonym. | Brak; wymaga samodzielnego napisania logiki przejść stanów w kodzie i bazie. |
| **Kontrola limitów (Rate Limiting)** | Wymaga stosowania zewnętrznego oprogramowania pośredniczącego (middleware) lub kolejki Redis. | Posiada wbudowaną, dojrzałą klasę AIORateLimiter automatycznie obsługującą limity14. | Wymaga ręcznej implementacji algorytmów kolejkowania i opóźnień (np. token bucket). |
| **Współpraca z FastAPI** | Bezproblemowa integracja; dostarcza gotowe mechanizmy do obsługi żądań webhookowych33. | Wymaga ręcznego bindowania pętli zdarzeń za pomocą asynchronicznego menedżera cyklu życia6. | Optymalna; brak jakiejkolwiek warstwy pośredniczącej, najniższe zużycie zasobów. |

**Rekomendacja technologiczna**: Dla systemu o strukturze "Router \+ Agenci za HTTP" najlepszym wyborem jest **aiogram 3.x**30. Oferuje on najlepsze wsparcie dla asynchronicznego routingu w FastAPI, posiada elastyczny system filtrów i middleware pozwalający na łatwe wstrzykiwanie zależności (np. sesji bazy danych), a jego wbudowana maszyna stanów pozwala na separację logiki biznesowej od technicznej obsługi protokołu Telegrama30.

### **Repozytoria open-source do adaptacji architektury**

* **openclaw/openclaw**: Dojrzały, rozbudowany system asystenta AI obsługujący integrację z wieloma kanałami komunikacyjnymi (w tym Telegram) oraz modularną strukturę ładowania umiejętności (skills) z rejestru ClawHub35. Pokazuje wzorcową separację warstwy sieciowej od biznesowej.  
* **shareAI-lab/claw0**: Repozytorium demonstrujące kompletną architekturę gatewaya wieloagentowego37. Zawiera wzorce izolacji sesji konwersacyjnych, dynamicznego routowania wiadomości w oparciu o stany oraz system kolejkowania wysyłek zapobiegający blokowaniu procesów roboczych37.  
* **hschickdevs/telegram-openai-agentkit**: Lekki wrapper integrujący python-telegram-bot z OpenAI Agents SDK38. Dostarcza doskonałe wzorce do dynamicznego rejestrowania i przełączania między wieloma przepływami (workflows) na jednego użytkownika przy użyciu prostych poleceń /upload i /activate38.  
* **sudoskys/telegramify-markdown**: Niezbędna biblioteka rozwiązująca problem bezpiecznego podziału sformatowanych odpowiedzi LLM na części poniżej 4096 znaków bez uszkadzania znaczników MarkdownV2/HTML25.

## **6\. Rekomendacja architektoniczna dla solo-przedsiębiorcy**

Wdrożenie i utrzymanie systemu modułowego przez jedną osobę, przy ograniczonym budżecie czasowym (2–4 godziny dziennie), wymaga wyboru architektury o minimalnym narzucie konfiguracyjnym i braku skomplikowanych zależności DevOps.

### **Opcje architektoniczne do oceny**

#### **Opcja A: Dynamic Monolith (Monolit z dynamicznym ładowaniem modułów)**

Aplikacja składa się z jednego serwisu FastAPI, w którym kod wszystkich agentów znajduje się w jednym repozytorium jako osobne pakiety Python. Router dynamicznie importuje i wywołuje odpowiednią klasę agenta na podstawie przypisania w bazie PostgreSQL. Asynchroniczność jest realizowana za pomocą wbudowanego mechanizmu asyncio.create\_task().

* **Plusy**: Skrajnie łatwe wdrożenie (jeden proces, jedno repozytorium), brak narzutu sieciowego na komunikację między serwisami, uproszczone debugowanie.  
* **Minusy**: Brak fizycznej izolacji procesów – błąd blokujący (np. pętla synchroniczna CPU) lub wyciek pamięci w kodzie jednego agenta może unieruchomić bota dla wszystkich użytkowników.  
* **Złożoność wdrożenia**: Bardzo niska (ok. 3–5 dni roboczych dla solo dewelopera).

#### **Opcja B: DB-Queue Distributed (FastAPI Router \+ PostgreSQL Task Queue \+ Python Workers)**

Router FastAPI działa jako bezstanowy przekaźnik6. Zapisuje on każde przychodzące zapytanie jako zadanie w tabeli agent\_jobs6. Każdy agent działa jako osobny, niezależny proces worker w języku Python (uruchamiany np. za pomocą systemd lub Docker Compose), który stale odpytuje tabelę zadań o nowe rekordy o statusie PENDING powiązane z jego agent\_id.

* **Plusy**: Pełna izolacja procesów (awaria kodu agenta SEO nie wpływa na działanie agenta copywritera). Brak konieczności wdrażania i utrzymywania zewnętrznych systemów kolejkowych typu RabbitMQ czy Redis39. Wszystkie dane o kolejkach i logach znajdują się w jednej bazie PostgreSQL, co ułatwia backupy i migracje.  
* **Minusy**: Opóźnienie rzędu kilkuset milisekund wynikające z częstotliwości odpytywania bazy danych przez procesy robocze (polling).  
* **Złożoność wdrożenia**: Niska do średniej (ok. 7–10 dni roboczych).

#### **Opcja C: Event-Driven Microservices (FastAPI \+ RabbitMQ \+ Dockerized Agent Services)**

Pełna, produkcyjna architektura mikroserwisowa40. Router FastAPI przesyła wiadomości do brokera komunikatów RabbitMQ, który zarządza dystrybucją zadań do dedykowanych kontenerów Docker reprezentujących poszczególnych agentów33.

* **Plusy**: Skrajnie wysoka odporność na błędy, natychmiastowe przetwarzanie zdarzeń w czasie rzeczywistym, łatwość skalowania horyzontalnego.  
* **Minusy**: Bardzo duży narzut operacyjny (konfiguracja i zabezpieczanie RabbitMQ, orkiestracja kontenerów, trudne debugowanie lokalne)5.  
* **Złożoność wdrożenia**: Ekstremalnie wysoka (powyżej 30 dni roboczych dla jednej osoby).

#### **Opcja D: Hybrid Gateway (n8n Webhook transport \+ FastAPI Router \+ Python Agents)**

Wykorzystanie n8n jako jedynego konsumenta webhooka z Telegrama (zastąpienie dotychczasowego 206-węzłowego monolitu prostym przepływem przekierowującym), który przesyła żądanie do routera FastAPI, a ten z kolei rozdziela zadania za pomocą wywołań HTTP POST (status 202\) bezpośrednio do aktywnych kontenerów agentów.

* **Plusy**: Wykorzystanie stabilnej i skonfigurowanej infrastruktury n8n do odbioru webhooków bez konieczności konfiguracji certyfikatów SSL bezpośrednio na poziomie FastAPI5.  
* **Minusy**: Wprowadzenie dodatkowego, krytycznego punktu awarii (n8n)12. Trudniejsze testowanie lokalne i brak natywnego kolejkowania w przypadku nagłego przestoju serwera agenta.  
* **Złożoność wdrożenia**: Średnia (ok. 10–14 dni roboczych).

### **Porównanie opcji architektonicznych dla solo-przedsiębiorcy**

| Parametr decyzji | Opcja A (Dynamic Monolith) | Opcja B (DB-Queue Distributed) | Opcja C (Event-Driven) | Opcja D (Hybrid Gateway) |
| :---- | :---- | :---- | :---- | :---- |
| **Czas wdrożenia (przy 2-4h/dzień)** | Ok. 1-2 tygodnie. | Ok. 2-3 tygodnie. | Powyżej 6-8 tygodni. | Ok. 2-3 tygodnie. |
| **Narzut konserwacyjny (DevOps)** | Minimalny (jeden proces VPS). | Niski (monitorowanie PostgreSQL \+ procesów workerów). | Bardzo wysoki (zarządzanie RabbitMQ, Docker, sieciami)5. | Średni (konieczność ciągłego utrzymania n8n i FastAPI)12. |
| **Koszt infrastruktury** | Skrajnie niski (najmniejszy VPS, minimalne zużycie RAM). | Niski (jeden serwer VPS z PostgreSQL i procesami tła). | Średni/Wysoki (wymaga zasobów pod brokera i kontenery)40. | Średni (n8n wymaga sporej alokacji pamięci RAM do stabilnego działania). |
| **Łatwość wdrażania nowych agentów** | Średnia (wymaga aktualizacji i restartu całej aplikacji). | Bardzo wysoka (wystarczy uruchomić nowy skrypt workera). | Wysoka (wymaga wdrożenia nowego obrazu Docker i kolejki)40. | Średnia (wymaga konfiguracji nowych tras HTTP POST). |

### **Rekomendacja i uzasadnienie wyboru**

Dla solo-przedsiębiorcy migrującego z n8n zaleca się wybór **Opcji B (DB-Queue Distributed)** jako architektury docelowej, z etapem przejściowym wykorzystującym **Opcję D (Hybrid Gateway)** w celu natychmiastowego uruchomienia systemu bez przestojów dla obecnych klientów.

#### **Dlaczego Opcja B jest optymalna?**

1. **Eliminacja długu technologicznego n8n**: Dotychczasowy przepływ n8n składający się z 206 węzłów jest skrajnie trudny w utrzymaniu, wersjonowaniu (brak łatwego podglądu diffów w gicie) oraz generuje wysokie koszty zasobów RAM na serwerze. Przeniesienie logiki do kodu w Pythonie drastycznie zwiększa stabilność systemu.  
2. **Niezawodność asynchroniczna bez skomplikowanego DevOps**: Wykorzystanie PostgreSQL jako kolejki zadań (agent\_jobs) całkowicie eliminuje potrzebę wdrażania systemów takich jak Celery czy RabbitMQ, których konfiguracja i zabezpieczenie przed utratą danych są czasochłonne dla jednego dewelopera39. Baza PostgreSQL, która i tak jest wymagana do przechowywania stanu sesji i subskrypcji klientów, idealnie nadaje się do roli brokera przy małej i średniej skali działalności.  
3. **Prawdziwa modularność biznesowa**: Wdrożenie nowego agenta, którego klient może dokupić jako moduł, polega wyłącznie na dodaniu rekordu do tabeli agent\_registry i uruchomieniu nowego, niezależnego skryptu workera. Jeśli kod nowego agenta ulegnie awarii (np. z powodu nieobsłużonego wyjątku z biblioteki LLM), przestanie działać wyłącznie ten jeden moduł. Cały rdzeń systemu, router FastAPI oraz pozostali agenci innych klientów będą działać bez jakichkolwiek zakłóceń, co ma kluczowe znaczenie przy oferowaniu stabilnego produktu komercyjnego (SaaS).

#### **Cytowane prace**

1. Updating Telegram Bot Commands In Realtime \- Stack Overflow, [https://stackoverflow.com/questions/66053613/updating-telegram-bot-commands-in-realtime](https://stackoverflow.com/questions/66053613/updating-telegram-bot-commands-in-realtime)  
2. setMyCommands \- aiogram 3.29.0 documentation, [https://docs.aiogram.dev/en/latest/api/methods/set\_my\_commands.html](https://docs.aiogram.dev/en/latest/api/methods/set_my_commands.html)  
3. Python Telegram API \-- how do I use ForceReply? \- Stack Overflow, [https://stackoverflow.com/questions/64916432/python-telegram-api-how-do-i-use-forcereply](https://stackoverflow.com/questions/64916432/python-telegram-api-how-do-i-use-forcereply)  
4. Telegram Bot API | Documentation | Postman API Network, [https://www.postman.com/aviation-physicist-17508953/ton-master/documentation/wnllsx2/telegram-bot-api](https://www.postman.com/aviation-physicist-17508953/ton-master/documentation/wnllsx2/telegram-bot-api)  
5. Self-built Telegram Bot customer service system vs SaaS platform: a comprehensive comparison of development, operation, and feature iteration | TG-Staff, [https://tg-staff.com/blog/self-hosted-bot-vs-tg-staff-saas/](https://tg-staff.com/blog/self-hosted-bot-vs-tg-staff-saas/)  
6. Application initialization \- Telegram Bot AI Integration Guide, [https://aotegaliyev.github.io/telegrambot-ai-integration-guide/app-guide/](https://aotegaliyev.github.io/telegrambot-ai-integration-guide/app-guide/)  
7. Telegram Limits — Telegram Info, [https://limits.tginfo.me/](https://limits.tginfo.me/)  
8. Bots FAQ \- Telegram APIs, [https://core.telegram.org/bots/faq](https://core.telegram.org/bots/faq)  
9. What is the limit of sending messages from a telegram bot \- Stack Overflow, [https://stackoverflow.com/questions/45905266/what-is-the-limit-of-sending-messages-from-a-telegram-bot](https://stackoverflow.com/questions/45905266/what-is-the-limit-of-sending-messages-from-a-telegram-bot)  
10. How to solve rate limit errors from Telegram Bot API with GramIO, [https://gramio.dev/rate-limits](https://gramio.dev/rate-limits)  
11. About Rate Limits | Poracle Documentation \- GitHub Pages, [https://muckelba.github.io/poracleWiki/operation/ratelimits.html](https://muckelba.github.io/poracleWiki/operation/ratelimits.html)  
12. Channels Bot Telegram: Your 2026 How-To Guide, [https://www.mava.app/blog/channels-bot-telegram](https://www.mava.app/blog/channels-bot-telegram)  
13. Limiting your API requests: the right way | by Alexander Bareyko | HackerNoon.com, [https://medium.com/hackernoon/limiting-your-api-requests-the-right-way-9608b661a0ce](https://medium.com/hackernoon/limiting-your-api-requests-the-right-way-9608b661a0ce)  
14. AIORateLimiter \- python-telegram-bot v22.0, [https://docs.python-telegram-bot.org/en/v22.0/telegram.ext.aioratelimiter.html](https://docs.python-telegram-bot.org/en/v22.0/telegram.ext.aioratelimiter.html)  
15. Support for Telegram bot-to-bot and guest-bot modes (Telegram May-7 2026 release) · Issue \#79077 \- GitHub, [https://github.com/openclaw/openclaw/issues/79077](https://github.com/openclaw/openclaw/issues/79077)  
16. setWebhook \- aiogram 3.16.0 documentation, [https://docs.aiogram.dev/en/v3.16.0/api/methods/set\_webhook.html](https://docs.aiogram.dev/en/v3.16.0/api/methods/set_webhook.html)  
17. Telegram.BotAPI 10.1.0 \- NuGet, [https://www.nuget.org/packages/Telegram.BotAPI](https://www.nuget.org/packages/Telegram.BotAPI)  
18. How verify request of webhook are from Telegram? \- Stack Overflow, [https://stackoverflow.com/questions/69882004/how-verify-request-of-webhook-are-from-telegram](https://stackoverflow.com/questions/69882004/how-verify-request-of-webhook-are-from-telegram)  
19. Telegram Ticket Bot: Automate Sales, Support & Scale Your, [https://ascn.ai/templates/telegram-ticket-bot-automation](https://ascn.ai/templates/telegram-ticket-bot-automation)  
20. Home \- telegram-send \- Pythonhosted.org, [https://pythonhosted.org/telegram-send/](https://pythonhosted.org/telegram-send/)  
21. telegram-send \- PyPI, [https://pypi.org/project/telegram-send/](https://pypi.org/project/telegram-send/)  
22. Message \- python-telegram-bot v22.0, [https://docs.python-telegram-bot.org/en/v22.0/telegram.message.html](https://docs.python-telegram-bot.org/en/v22.0/telegram.message.html)  
23. Split output to multiple messages (below 4096 char.) : r/n8n \- Reddit, [https://www.reddit.com/r/n8n/comments/1iiombf/split\_output\_to\_multiple\_messages\_below\_4096\_char/](https://www.reddit.com/r/n8n/comments/1iiombf/split_output_to_multiple_messages_below_4096_char/)  
24. Handling Markdown in Large Text Messages with pyTelegramBotAPI \#2149 \- GitHub, [https://github.com/eternnoir/pyTelegramBotAPI/discussions/2149](https://github.com/eternnoir/pyTelegramBotAPI/discussions/2149)  
25. telegramify-markdown \- PyPI, [https://pypi.org/project/telegramify-markdown/](https://pypi.org/project/telegramify-markdown/)  
26. sudoskys/telegramify-markdown: Markdown To Telegram MarkdownV2 Converter Python| No more worrying about formatting. \- GitHub, [https://github.com/sudoskys/telegramify-markdown](https://github.com/sudoskys/telegramify-markdown)  
27. Creating a Conversational Telegram Bot in Node.js \- Level Up Coding, [https://levelup.gitconnected.com/creating-a-conversational-telegram-bot-in-node-js-with-a-finite-state-machine-and-async-await-ca44f03874f9](https://levelup.gitconnected.com/creating-a-conversational-telegram-bot-in-node-js-with-a-finite-state-machine-and-async-await-ca44f03874f9)  
28. Message contains quote from the bot when I send it using custom keyboard \- Stack Overflow, [https://stackoverflow.com/questions/37149470/message-contains-quote-from-the-bot-when-i-send-it-using-custom-keyboard](https://stackoverflow.com/questions/37149470/message-contains-quote-from-the-bot-when-i-send-it-using-custom-keyboard)  
29. Is accessing details of message replied from another chat possible \- Stack Overflow, [https://stackoverflow.com/questions/79701294/is-accessing-details-of-message-replied-from-another-chat-possible](https://stackoverflow.com/questions/79701294/is-accessing-details-of-message-replied-from-another-chat-possible)  
30. aiogram \- aiogram, [https://aiogram.dev/](https://aiogram.dev/)  
31. How to build a Crypto Price Change Signal Bot on Telegram \- Bitquery Docs, [https://docs.bitquery.io/docs/usecases/price-change-signal-bot/](https://docs.bitquery.io/docs/usecases/price-change-signal-bot/)  
32. AIORateLimiter \- python-telegram-bot v21.5, [https://docs.python-telegram-bot.org/en/v21.5/telegram.ext.aioratelimiter.html](https://docs.python-telegram-bot.org/en/v21.5/telegram.ext.aioratelimiter.html)  
33. Telegram bot for table booking on webhooks: FastAPI, Aiogram Dialog, FastStream and RabbitMQ in a single ecosystem | by Amverum Cloud | Medium, [https://medium.com/@amverait/friends-hello-8460dfe86ef1](https://medium.com/@amverait/friends-hello-8460dfe86ef1)  
34. Webhook \- aiogram 3.27.0 documentation, [https://docs.aiogram.dev/en/v3.27.0/dispatcher/webhook.html](https://docs.aiogram.dev/en/v3.27.0/dispatcher/webhook.html)  
35. ClawHub \- OpenClaw Docs, [https://docs.openclaw.ai/clawhub](https://docs.openclaw.ai/clawhub)  
36. OpenClaw — Personal AI Assistant \- GitHub, [https://github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)  
37. shareAI-lab/claw0: 0 \- 1 learn OpenClaw: sections to build an claw-AI agent from scratch, [https://github.com/shareAI-lab/claw0](https://github.com/shareAI-lab/claw0)  
38. hschickdevs/telegram-openai-agentkit \- GitHub, [https://github.com/hschickdevs/telegram-openai-agentkit](https://github.com/hschickdevs/telegram-openai-agentkit)  
39. My workflow won't publish \- Questions \- n8n Community, [https://community.n8n.io/t/my-workflow-wont-publish/301018](https://community.n8n.io/t/my-workflow-wont-publish/301018)  
40. All-in-One FastAPI Telegram Mini-App API \- GitHub, [https://github.com/zytfo/fastapi-telegram-mini-app](https://github.com/zytfo/fastapi-telegram-mini-app)