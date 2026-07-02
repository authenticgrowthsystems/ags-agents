# CM_RESEARCH_manus.md
## Produkcyjne wzorce dla Telegram bota jako UI sieci agentów AI (AGS)

**Data:** 2026-07-02 | **Stos docelowy:** Python FastAPI + PostgreSQL + Telegram Bot API + n8n (transport)

---

## 1. Przełączanie kontekstu agentów w jednym bocie

### Per-chat state w bazie danych

Telegram nie posiada wbudowanej koncepcji "aktywnego agenta". Każda wiadomość od użytkownika jest bezstanowym zdarzeniem HTTP. Izolacja kontekstu musi być zaimplementowana po stronie aplikacji, kluczując stan parą `(chat_id, user_id)` w PostgreSQL [1].

Minimalna tabela stanu dla AGS:

```sql
-- PostgreSQL
CREATE TABLE user_agent_state (
    chat_id      BIGINT NOT NULL,
    user_id      BIGINT NOT NULL,
    active_agent VARCHAR(50) NOT NULL DEFAULT 'menu',  -- 'cm', 'manager', 'x'
    fsm_state    VARCHAR(100),                          -- np. 'awaiting_approval'
    fsm_data     JSONB,                                 -- kontekst stanu (draft_id, etc.)
    updated_at   TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (chat_id, user_id)
);
```

Router w FastAPI sprawdza `active_agent` przed delegowaniem do serwisu agenta:

```python
# aiogram 3.x + FastAPI, router.py
from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def universal_handler(message: Message, db_session):
    state = await db_session.get_user_state(message.chat.id, message.from_user.id)
    
    if state.active_agent == "cm":
        await cm_agent_service.handle(message, state)
    elif state.active_agent == "manager":
        await manager_agent_service.handle(message, state)
    else:
        await show_main_menu(message)
```

### setMyCommands i BotCommandScope

Telegram API udostępnia metodę `setMyCommands` z parametrem `scope` [2]. Pozwala to na dynamiczną zmianę menu komend widocznych dla konkretnego użytkownika (podpowiadanych po wpisaniu `/`). Gdy klient AGS kupuje nowy moduł (np. CM Agent), system wywołuje:

```python
# aiogram 3.x
from aiogram.types import BotCommand, BotCommandScopeChat

async def activate_agent_for_user(bot, chat_id: int, agent_slug: str):
    """Wywołane po zakupie modułu przez klienta."""
    base_commands = [
        BotCommand(command="start", description="Menu główne"),
        BotCommand(command="cancel", description="Anuluj bieżące działanie"),
    ]
    agent_commands = {
        "cm": [BotCommand(command="cm", description="Content Manager Agent")],
        "manager": [BotCommand(command="manager", description="Manager Agent")],
        "x": [BotCommand(command="x", description="X (Twitter) Agent")],
    }
    commands = base_commands + agent_commands.get(agent_slug, [])
    await bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeChat(chat_id=chat_id)
    )
```

Zakres `BotCommandScopeChat` nadpisuje domyślne menu wyłącznie dla wskazanego `chat_id`. Limit to 100 komend na scope [2].

### Inline vs Reply Keyboards

**Reply Keyboards** zastępują systemową klawiaturę telefonu. Są odpowiednie do głównej nawigacji ("Wróć do menu", "Anuluj"), ponieważ są zawsze widoczne. Ich wadą jest zaśmiecanie historii czatu (każde naciśnięcie przycisku wysyła wiadomość tekstową).

**Inline Keyboards** są podpięte pod konkretną wiadomość bota. Rekomendowane dla akcji specyficznych dla agenta (zatwierdzanie treści, wybór opcji), ponieważ nie generują nowych wiadomości, a callback jest obsługiwany cicho [3]. Dla AGS: inline keyboards do HITL, reply keyboards do nawigacji.

### Deep-linking

Mechanizm `start=` w URL bota (`https://t.me/moj_bot?start=agent_cm_preview_abc123`) pozwala na wysłanie użytkownikowi linku (z n8n, maila, powiadomienia), który po kliknięciu otwiera bota i automatycznie przełącza kontekst na konkretne zadanie [4]. Parametr `start` jest przekazywany jako argument do handlera `/start`.

```python
# aiogram 3.x, deep-link handler
from aiogram.filters import CommandStart, CommandObject

@router.message(CommandStart(deep_link=True))
async def deep_link_handler(message: Message, command: CommandObject, db_session):
    # command.args = "agent_cm_preview_abc123"
    parts = command.args.split("_")  # ["agent", "cm", "preview", "abc123"]
    if parts[0] == "agent" and len(parts) >= 2:
        await db_session.set_active_agent(message.chat.id, message.from_user.id, parts[1])
        await message.answer(f"Przełączono na agenta: {parts[1].upper()}")
```

### Przykłady z produkcji ("mom test")

Wzorzec jednego bota z wieloma kontekstami jest stosowany przez boty takie jak **@BotFather** (Telegram) i **@Manybot**. Użytkownik przełącza "tryb" komendą, a bot odpowiada w kontekście aktywnego modułu. Kluczowe jest, aby po przełączeniu kontekstu bot zawsze potwierdził zmianę prostym komunikatem: "Jesteś teraz w trybie Content Manager. Wyślij mi temat posta."

---

## 2. Wzorzec Two-bot vs Kanał Telegram

### Porównanie opcji

| Kryterium | Two-bot (interaktywny + notyfikacje) | Prywatny kanał | Forum Topics (supergrupa) |
| :--- | :--- | :--- | :--- |
| **Izolacja kontekstu** | Dwa oddzielne czaty | Brak (jeden strumień) | Pełna (thread_id per agent) |
| **Limity API** | Oddzielne (2x 30 msg/s) | Wspólne z botem | Wspólne z botem |
| **Interaktywność** | Pełna w obu botach | Ograniczona (callbacki trafiają do bota) | Pełna w każdym wątku |
| **UX dla Tomasza** | Dwa boty do zarządzania | Jeden kanał, jeden bot | Jedna supergrupa, jeden bot |
| **Przeszukiwalność logów** | Osobny czat z botem 2 | Tak (kanał) | Tak (wątki) |
| **Złożoność wdrożenia** | Umiarkowana (2 tokeny) | Niska | Umiarkowana (konfiguracja supergrupy) |

### Limity API Telegrama

Telegram nie publikuje oficjalnie dokładnych limitów. Wartości empiryczne [5]:

- Wiadomości do **tego samego czatu**: ~1/sekundę
- Wiadomości do **różnych czatów**: ~30/sekundę globalnie
- Operacje na grupach/kanałach: niższe, zależne od liczby członków
- Przekroczenie limitu: HTTP 429 z polem `retry_after` (do 35+ sekund blokady całego bota)
- Płatny broadcast (`allow_paid_broadcast=True`): do 1000/sekundę za 0.1 Stars/msg [5]

### Wzorzec Two-bot: kiedy stosować

Wzorzec dwóch botów (jeden interaktywny, jeden do logów/powiadomień) ma sens, gdy:
- Logi są bardzo częste (ryzyko przekroczenia limitu 1 msg/s w jednym czacie)
- Chcemy umożliwić wyciszenie powiadomień bez utraty interaktywności
- Różne osoby mają dostęp do różnych botów (np. Tomasz + asystent)

Wada krytyczna dla Stage 0-1: użytkownik musi zarządzać dwoma botami, co psuje "mom test".

### Forum Topics: rekomendacja dla AGS

Wzorzec spopularyzowany przez systemy OpenClaw i `pavel-molyanov/telegram-ai-agent` [6]. Jeden bot w supergrupie z włączonymi Forum Topics. Każdy agent (lub projekt) otrzymuje własny wątek (Topic), np. `#CM-Agent`, `#X-Agent`, `#System-Logs`. Telegram nadaje każdemu Topic unikalne `message_thread_id`, które jest przekazywane w każdym Update. Router może na tej podstawie delegować do odpowiedniego agenta.

```python
# Routing na podstawie thread_id w supergrupie
THREAD_TO_AGENT = {
    123: "cm_agent",   # thread_id wątku CM
    456: "x_agent",    # thread_id wątku X
}

@router.message()
async def supergroup_router(message: Message):
    agent = THREAD_TO_AGENT.get(message.message_thread_id)
    if agent:
        await dispatch_to_agent(agent, message)
```

Ograniczenie: wymaga supergrupy (nie zwykłej grupy ani prywatnego czatu). Dla Tomasza jako solo foundera, który chce prostego 1:1, lepszym startem jest Opcja 4 (patrz Rekomendacja).

---

## 3. Routing wiadomości: webhook -> router -> agent

### Architektura asynchroniczna (202 Accepted)

Telegram wymaga odpowiedzi 2xx w ciągu 60 sekund, w przeciwnym razie ponawia dostarczenie Update [7]. Przy długich operacjach AI (generowanie treści, analiza) wzorzec 202 Accepted jest obowiązkowy:

```
Telegram -> POST /webhook -> FastAPI (weryfikacja + zapis do kolejki) -> 202 Accepted
                                                                            |
                                                          asyncio.create_task() lub Celery
                                                                            |
                                                          Agent Worker (przetwarza, ~5-30s)
                                                                            |
                                                          POST /sendMessage -> Telegram -> Użytkownik
```

Implementacja w FastAPI z aiogram 3.x:

```python
# main.py - FastAPI + aiogram 3.x webhook
import asyncio
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.types import Update

app = FastAPI()
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

WEBHOOK_SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]

@app.post("/webhook")
async def telegram_webhook(request: Request):
    # 1. Weryfikacja tokenu (bezpieczeństwo)
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret token")
    
    # 2. Deduplikacja update_id
    data = await request.json()
    update_id = data.get("update_id")
    if await db.is_update_processed(update_id):
        return {"ok": True}  # Idempotent - już przetworzone
    await db.mark_update_as_processed(update_id)
    
    # 3. Asynchroniczne przetwarzanie - nie blokujemy webhooka
    update = Update.model_validate(data)
    asyncio.create_task(dp.process_update(update))
    
    return {"ok": True}  # 200 natychmiast
```

### Bezpieczeństwo webhooka

Podczas rejestracji webhooka (`setWebhook`) należy podać `secret_token`. Telegram dołącza go do każdego żądania w nagłówku `X-Telegram-Bot-Api-Secret-Token` [9]. Alternatywnie można ograniczyć dostęp do podsieci Telegrama: `149.154.160.0/20` i `91.108.4.0/22` [9].

Gotowa biblioteka do FastAPI: `fastapi-security-telegram-webhook` [9b] (28 gwiazdek na GitHub):

```python
# pip install fastapi-security-telegram-webhook
from fastapi_security_telegram_webhook import OnlyTelegramNetworkWithSecret

webhook_security = OnlyTelegramNetworkWithSecret(real_secret="twoj-secret")

@app.post("/webhook/{secret}", dependencies=[Depends(webhook_security)])
async def process_update(update_raw=Body(...)):
    ...
```

### Deduplikacja (Idempotency)

`update_id` jest globalnie unikalny dla danego bota i nigdy się nie powtarza [10]. Schemat deduplikacji w PostgreSQL:

```sql
CREATE TABLE processed_updates (
    update_id  BIGINT PRIMARY KEY,
    processed_at TIMESTAMPTZ DEFAULT now()
);
-- Czyszczenie starszych niż 24h (Telegram trzyma updates max 24h)
DELETE FROM processed_updates WHERE processed_at < now() - INTERVAL '24 hours';
```

### Routing do agentów (HTTP POST 202)

```python
# agent_router.py
import httpx

AGENT_ENDPOINTS = {
    "cm":      "http://cm-agent:8001/process",
    "manager": "http://manager-agent:8002/process",
    "x":       "http://x-agent:8003/process",
}

async def dispatch_to_agent(agent_slug: str, payload: dict, chat_id: int):
    """Fire-and-forget do serwisu agenta. Agent odpowiada przez sendMessage."""
    url = AGENT_ENDPOINTS.get(agent_slug)
    if not url:
        return
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            await client.post(url, json={
                "chat_id": chat_id,
                "payload": payload,
            })
        except httpx.TimeoutException:
            # Agent niedostępny - poinformuj użytkownika
            await bot.send_message(chat_id, "⚠️ Agent chwilowo niedostępny. Spróbuj za chwilę.")
```

### Dzielenie wiadomości (4096 znaków)

`sendMessage` i `editMessageText` mają limit 4096 znaków UTF-8 [11]. Dłuższe treści (np. wygenerowane posty z analizą) muszą być dzielone:

```python
def split_message(text: str, max_len: int = 4096) -> list[str]:
    """Dzieli tekst na granicach akapitów, nie w środku słowa."""
    if len(text) <= max_len:
        return [text]
    
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Szukaj ostatniego \n\n przed limitem
        split_at = text.rfind("\n\n", 0, max_len)
        if split_at == -1:
            split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    return chunks
```

### editMessageText z przyciskami (wzorzec "Loading")

Zamiast wysyłać nową wiadomość, bot edytuje istniejącą. Daje to wrażenie "żywej" odpowiedzi:

```python
# aiogram 3.x
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def send_draft_for_approval(bot: Bot, chat_id: int, draft: str):
    # 1. Wyślij placeholder
    msg = await bot.send_message(chat_id, "⏳ Generuję treść...")
    
    # 2. Agent przetwarza (async)
    # ... (wywoływane przez agenta po zakończeniu)
    
    # 3. Edytuj z wynikiem i przyciskami
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Zatwierdź", callback_data="approve"),
            InlineKeyboardButton(text="❌ Odrzuć", callback_data="reject"),
        ],
        [
            InlineKeyboardButton(text="✏️ Edytuj", callback_data="edit"),
            InlineKeyboardButton(text="🔄 Inny kąt", callback_data="different_angle"),
        ],
    ])
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg.message_id,
        text=f"📝 Propozycja treści:\n\n{draft}",
        reply_markup=keyboard,
    )
```

---

## 4. Konwersacyjny Human-in-the-Loop (HITL)

### Dlaczego same przyciski nie wystarczą

Przyciski inline "Zatwierdź/Odrzuć" obsługują tylko binarne decyzje. Dla AGS kluczowy jest feedback jakościowy: "Napisz to bardziej energetycznie", "Skróć do 280 znaków", "Zmień perspektywę na klienta". Wymaga to maszyny stanów, która przechwytuje swobodne wiadomości tekstowe jako instrukcje dla agenta.

### FSM z aiogram 3.x i PostgreSQL

```python
# states.py - aiogram 3.x
from aiogram.fsm.state import State, StatesGroup

class ContentApprovalStates(StatesGroup):
    awaiting_approval = State()   # Bot czeka na decyzję użytkownika
    awaiting_edit     = State()   # Użytkownik wpisuje instrukcję edycji
    awaiting_angle    = State()   # Użytkownik opisuje nowy kąt
```

```python
# handlers/approval.py - aiogram 3.x
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

router = Router()

# Callback: użytkownik kliknął "Zatwierdź"
@router.callback_query(F.data == "approve", ContentApprovalStates.awaiting_approval)
async def handle_approve(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await publish_content(data["draft_id"])
    await state.clear()
    await callback.message.edit_text("✅ Treść opublikowana!")
    await callback.answer()

# Callback: użytkownik kliknął "Edytuj"
@router.callback_query(F.data == "edit", ContentApprovalStates.awaiting_approval)
async def handle_edit_request(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ContentApprovalStates.awaiting_edit)
    await callback.message.reply(
        "Napisz instrukcję edycji (np. 'Skróć do 280 znaków i dodaj CTA'):",
        reply_markup=ForceReply(selective=True)
    )
    await callback.answer()

# Wiadomość tekstowa: użytkownik podał instrukcję edycji
@router.message(ContentApprovalStates.awaiting_edit)
async def handle_edit_instruction(message: Message, state: FSMContext):
    data = await state.get_data()
    instruction = message.text
    # Przekaż instrukcję do agenta
    await dispatch_to_agent("cm", {
        "action": "regenerate",
        "draft_id": data["draft_id"],
        "instruction": instruction,
    }, message.chat.id)
    await state.set_state(ContentApprovalStates.awaiting_approval)
    await message.answer("⏳ Generuję poprawioną wersję...")

# ESCAPE: /cancel działa z KAŻDEGO stanu
@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("Nie ma nic do anulowania.")
        return
    await state.clear()
    await message.answer("❌ Anulowano. Wróć do menu: /start", reply_markup=ReplyKeyboardRemove())
```

### ForceReply: kiedy i jak

`ForceReply` zmusza klienta Telegrama do automatycznego otwarcia interfejsu odpowiedzi na konkretną wiadomość [13]. Jest kluczowy w supergrupach (bot w trybie privacy widzi tylko wiadomości adresowane do niego lub odpowiedzi na jego wiadomości). W konwersacjach prywatnych 1:1, klasyczne FSM jest wystarczające i prostsze.

```python
# aiogram 3.x - ForceReply w supergrupie
from aiogram.types import ForceReply

await message.answer(
    "Opisz nowy kąt dla tego posta:",
    reply_markup=ForceReply(selective=True, input_field_placeholder="np. Z perspektywy klienta...")
)
```

### Wzorzec z n8n (Pauza i Wznowienie)

W architekturze AGS, gdzie n8n pełni rolę transportu webhooków, wzorzec zatwierdzania wygląda następująco [14]:

1. n8n generuje treść i wysyła ją do bota (POST do FastAPI).
2. Bot wysyła treść użytkownikowi z przyciskami i przechodzi w stan `awaiting_approval`.
3. n8n zawiesza workflow na węźle "Wait for Webhook" z unikalnym `execution_id`.
4. Użytkownik klika "Zatwierdź" lub wpisuje instrukcję.
5. Bot wysyła POST do n8n (`/webhook/resume/{execution_id}`) z decyzją użytkownika.
6. n8n wznawia workflow i publikuje treść lub generuje nową wersję.

Koszt: ~$0.003 za wykonanie z gpt-4o-mini. Odrzucenia spadają z ~30% do ~10% po dodaniu kilku przykładów do promptu [14].

---

## 5. Porównanie bibliotek i Open-Source

### aiogram 3.x vs python-telegram-bot v21+

| Kryterium | aiogram 3.27.x | python-telegram-bot v21.x |
| :--- | :--- | :--- |
| **Architektura** | W pełni asyncio, nowoczesna | Async od v20, sync wrapper wciąż dostępny |
| **Routing / Modułowość** | System Routerów (analogiczny do FastAPI) | Dispatcher + Handlery |
| **FSM (State Machine)** | Natywne `StatesGroup`, adaptery: MemoryStorage, RedisStorage, custom | `ConversationHandler` **nie działa w środowiskach wieloprocesowych** (FastAPI + Gunicorn/Uvicorn) [15] |
| **Integracja z FastAPI** | Natywna, przez `SimpleRequestHandler` lub `aiogram-webhook` | Możliwa, ale wymaga obejść |
| **Wydajność** | Bardzo niska latencja, stworzony pod webhooki | Nieco cięższy narzut |
| **Społeczność (2026)** | Szybko rosnąca, aktywna | Większy ekosystem, więcej legacy przykładów |
| **Krytyczny bug** | Brak znanych blokujących bugów | Issue #5225: ConversationHandler nie działa z wieloma procesami [15] |

**Rekomendacja:** `aiogram 3.x`. Krytyczny bug PTB (issue #5225 [15]) sprawia, że `ConversationHandler` jest bezużyteczny w architekturze FastAPI z wieloma workerami uvicorn. Aiogram nie ma tego problemu, ponieważ FSMContext jest read-through do backendu (Redis/PostgreSQL) przy każdym update.

### Projekty Open-Source warte analizy

Poniżej 5 repozytoriów z konkretnymi wzorcami do skopiowania:

**1. langchain-ai/social-media-agent** (2.6k gwiazdek, TypeScript)
Repozytorium: https://github.com/langchain-ai/social-media-agent

Co skopiować: Wzorzec HITL dla mediów społecznościowych. Agent generuje posty na Twitter i LinkedIn, a użytkownik zatwierdza, odrzuca lub modyfikuje przez interfejs "Agent Inbox". Implementuje pełny cykl: generowanie -> zatwierdzanie -> publikacja. Wzorzec `interrupt()` z LangGraph (odpowiednik FSM) jest bezpośrednio przenoszalny na Telegram.

**2. pavel-molyanov/telegram-ai-agent** (63 gwiazdki, Python)
Repozytorium: https://github.com/pavel-molyanov/telegram-ai-agent

Co skopiować: Użycie Forum Topics jako izolowanych kontekstów dla różnych agentów. Każdy Topic ma własny `cwd`, `mode`, `engine`. Konfiguracja per-topic w `topic_config.json` (kluczowana przez `message_thread_id`). Wzorzec "live stream" (edytowanie jednej wiadomości z postępem zamiast spamowania nowymi). Komendy `/mode`, `/engine`, `/stream` do zmiany zachowania agenta bez wychodzenia z czatu.

**3. vlymar1/aiogram-bot-template** (Python)
Repozytorium: https://github.com/vlymar1/aiogram-bot-template

Co skopiować: Produkcyjna struktura modularna dla aiogram 3.x z PostgreSQL (SQLAlchemy), Redis, Docker Compose i wbudowanym panelem admina. Wzorzec organizacji kodu: `handlers/`, `states/`, `keyboards/`, `middlewares/`, `services/`. Gotowy punkt startowy dla AGS.

**4. BushlanovDev/aiogram-fastapi-bot-template** (Python)
Repozytorium: https://github.com/BushlanovDev/aiogram-fastapi-bot-template

Co skopiować: Minimalna, czysta integracja aiogram 3.x z FastAPI przez webhooki. Struktura projektu: `bot/` (logika bota) + `webapp/` (FastAPI). Dobry punkt startowy dla AGS zanim dodamy pełen stack.

**5. old-juniors/fastgram** (Python)
Repozytorium: https://github.com/old-juniors/fastgram

Co skopiować: Pełny stos produkcyjny: FastAPI + aiogram 3 + SQLAlchemy + PostgreSQL + Redis + Celery. Wzorzec kolejkowania zadań przez Celery (zamiast `asyncio.create_task()`), co daje persistencję przy restartach serwisu.

---

## Rekomendacja Architektury

Poniżej 4 opcje architektoniczne dla AGS. Kontekst: Stage 0-1, solo founder, 2-4h/dziennie, ADHD, priorytet "works in production w dniach".

### Opcja 1: N8n-Driven (No-code)

**Opis:** Bot obsługiwany całkowicie przez węzły Telegram w n8n. Logika agentów również w n8n (LLM nodes, HTTP Request nodes).

**Plusy:** Najszybszy start (godziny). Wizualne debugowanie przepływów. Brak kodu Python do pisania.

**Minusy:** Brak izolacji stanu FSM między agentami. Trudne zarządzanie kontekstem wielu agentów. Niezgodne z docelowym stosem (Python). Koszmar w utrzymaniu przy wzroście złożoności powyżej ~50 węzłów.

**Złożoność dla solo foundera:** Niska na start, eksponencjalnie rosnąca.

### Opcja 2: Python PTB Polling (Szybki prototyp)

**Opis:** Aplikacja Python z `python-telegram-bot` w trybie `getUpdates` (polling). Jeden skrypt, brak webhooków.

**Plusy:** Brak konieczności konfiguracji domen i SSL. Szybkie iteracje lokalne. Dobry do testowania logiki agentów.

**Minusy:** Architektura nieprodukcyjna (downtime przy restartach). Krytyczny bug `ConversationHandler` w środowiskach wieloprocesowych [15]. Brak skalowalności.

**Złożoność dla solo foundera:** Niska, ale pułap jest niski.

### Opcja 3: Aiogram + FastAPI + Supergrupa z Forum Topics

**Opis:** W pełni modularny system. Jeden bot w supergrupie z Forum Topics. Każdy moduł agenta (CM, X) to osobny wątek. FastAPI odbiera webhooki, Redis jako kolejka, Celery jako worker.

**Plusy:** Najlepszy UX dla wielu agentów (wizualna separacja). Produkcyjna wydajność. Pełna izolacja kontekstu przez `thread_id`.

**Minusy:** Wymaga konfiguracji supergrupy, Redis, Celery, PostgreSQL, domeny z SSL. Zajmie 2-3 tygodnie na stabilne wdrożenie dla solo foundera.

**Złożoność dla solo foundera:** Wysoka na start, liniowo rosnąca.

### Opcja 4: Aiogram + FastAPI Webhook + Inline Context (ZALECANA)

**Opis:** Jeden bot, prywatna konwersacja 1:1 z Tomaszem. FastAPI jako brama webhookowa, weryfikująca `X-Telegram-Bot-Api-Secret-Token`. Logika oparta na `aiogram 3.x` z FSM w PostgreSQL. Zmiana agenta przez komendy `/cm`, `/manager`, które aktualizują `active_agent` w bazie i wywołują `setMyCommands` dla danego `chat_id`. Każdy agent to osobny FastAPI worker service (zgodnie ze specyfikacją AGS).

**Plusy:**
- Produkcyjna architektura webhookowa od pierwszego dnia.
- Brak problemów PTB z wieloprocesowością (aiogram).
- Spełnia "mom test" (prosty czat 1:1, bez konfiguracji supergrupy).
- Asynchroniczne przetwarzanie (202 Accepted) dla długich operacji AI.
- Modularność: nowy agent = nowy serwis + nowa komenda w `setMyCommands`.
- Gotowy szablon: `vlymar1/aiogram-bot-template` lub `BushlanovDev/aiogram-fastapi-bot-template`.

**Minusy:** Wymaga napisania routera w Pythonie. Brak wizualnej separacji kontekstów (wszystko w jednym czacie).

**Złożoność dla solo foundera:** Umiarkowana. Szkielet działa w 1-2 dni na gotowym szablonie.

**WYBÓR: Opcja 4**

Uzasadnienie: Opcja 4 jest kanoniczna ze specyfikacją AGS (kierunek: bot = UI, brain = Python). `aiogram 3.x` omija krytyczny bug PTB w środowiskach webhookowych (issue #5225). Architektura czatu 1:1 z zarządzaniem stanem w PostgreSQL dostarcza wartość biznesową najszybciej (Stage 0-1), bez narzutu konfiguracyjnego supergrupy. Migracja z n8n (206 węzłów) do Pythona jest stopniowa: n8n pozostaje jako transport webhooków, a logika agentów przenosi się do Pythona serwis po serwisie.

**Pierwszy konkretny krok:** Sklonuj `BushlanovDev/aiogram-fastapi-bot-template`, dodaj tabelę `user_agent_state` w PostgreSQL, zaimplementuj handler `/cm` z `setMyCommands(scope=BotCommandScopeChat)` i `asyncio.create_task()` jako placeholder dla CM agenta. ETA: 4-6h.

---

## References

[1] https://medium.com/sp-lutsk/exploring-finite-state-machine-in-aiogram-3-a-powerful-tool-for-telegram-bot-development-9cd2d19cfae9 -- "Exploring Finite State Machine in Aiogram 3", SP-Lutsk, 2024

[2] https://core.telegram.org/bots/api#botcommandscope -- Telegram Bot API: BotCommandScope, oficjalna dokumentacja

[3] https://core.telegram.org/bots/features -- Telegram Bot Features: Keyboards, Commands, Deep Linking

[4] https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/deeplinking.py -- PTB deep-linking example

[5] https://gramio.dev/rate-limits -- GramIO: Rate Limits, empiryczne limity API Telegrama, 2026

[6] https://github.com/pavel-molyanov/telegram-ai-agent -- pavel-molyanov/telegram-ai-agent, wzorzec Forum Topics

[7] https://core.telegram.org/bots/api -- Telegram Bot API: setWebhook, timeout behavior

[8] https://core.telegram.org/bots/faq -- Telegram Bots FAQ: rate limits, retry behavior

[9] https://www.glukhov.org/app-architecture/integration-patterns/implementing-telegram-bot-python-javascript/ -- "Implementing Telegram Bot in Python", Glukhov.org

[9b] https://github.com/b0g3r/fastapi-security-telegram-webhook -- fastapi-security-telegram-webhook library

[10] https://stackoverflow.com/questions/72402693/in-telegram-bot-api-update-object-can-update-id-be-ever-repeated -- "Can update_id be repeated?", Stack Overflow

[11] https://core.telegram.org/bots/api#sendmessage -- Telegram Bot API: sendMessage, limit 4096 chars

[12] https://github.com/langchain-ai/social-media-agent -- langchain-ai/social-media-agent, HITL pattern

[13] https://docs.python-telegram-bot.org/en/v22.6/telegram.forcereply.html -- PTB: ForceReply documentation

[14] https://www.reddit.com/r/n8n/comments/1scio1u/i_built_a_reusable_telegram_approval_bot_for_n8n/ -- "Reusable Telegram approval bot for n8n", Reddit r/n8n, 2026

[15] https://github.com/python-telegram-bot/python-telegram-bot/issues/5225 -- PTB Issue #5225: ConversationHandler unusable in multi-process deployments, 2026
