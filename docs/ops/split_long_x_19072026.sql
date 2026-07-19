-- Ciecie 6 dlugich X-ow na serie samodzielnych postow (Tomasz 19/07: 'sam to potniesz,
-- grafika tylko przy pierwszej czesci'). Czesc 1 = UPDATE (media zostaja); 2+ = INSERT bez mediow.
-- Sloty: ludzkie minuty, okno X 13:00-22:00, gap >=60 min; #224 rozlozony na 30-31/07.
BEGIN;

-- #175: 1535 zn -> 4 czesci
UPDATE post_queue SET content = $p175$Your API bill arrived. One line item towers over the rest. You don't immediately know why.

You dig through logs, task by task, until the picture emerges.

The reflex is to hunt cheaper. Smaller model. Shorter prompt. Fewer calls. That fixes the symptom, not the cause.

Cost per task isn't just a number to shrink. It's diagnostic data. When one task costs ten times more than similar ones, your system is doing something it shouldn't.$p175$ WHERE id = 175;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p175$Maybe the agent reads the entire document instead of a fragment because no one designed a context retrieval mechanism. Maybe the task bounces between two agents because their responsibility boundary is blurred. Maybe the model gets insufficient context on the first try and re-queries, this time with full history appended.

In each case, high cost isn't a financial problem. It's a map showing which part of your architecture is poorly designed.$p175$, brand, platform, topic, status, content_item_id, '2026-07-20 17:41+02', '[]'::jsonb
FROM post_queue WHERE id = 175;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p175$This requires concrete work. You need to design the system so cost per task is visible at every step, not just on the monthly invoice. Without it you see only the sum and guess what's inflating it.

The same logic works when hunting bugs. When something breaks and needs repair, the first question isn't "how much did this cost". It's "why did this task need so many resources to execute". The answer usually points straight to where your architecture has a hole.$p175$, brand, platform, topic, status, content_item_id, '2026-07-20 19:23+02', '[]'::jsonb
FROM post_queue WHERE id = 175;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p175$Remember: read cost per task as diagnosis, not as a bill. The bill tells you what you paid. The diagnosis tells you what to fix so next time you pay less for the same task done better.$p175$, brand, platform, topic, status, content_item_id, '2026-07-20 20:58+02', '[]'::jsonb
FROM post_queue WHERE id = 175;

-- #204: 1478 zn -> 3 czesci
UPDATE post_queue SET content = $p204$Agent returned error 422. Technically correct.

Means nothing to the user.

Picture this: client fills a form, agent queries the API, data structure doesn't match, system responds per spec. Unprocessed entity. Validation failed.

Client sees the message and has no idea what to do next. Is it their mistake? System mistake? Retry? Wait? Contact support?

That's the gap between a technical error and a user error. One tells the machine what broke in the request structure. The other should tell the human what to do now.$p204$ WHERE id = 204;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p204$Most agents don't separate them. They return whatever the API gave them or their own validation logic, one-to-one. Looks like saved work. Actually shifts the entire cost of interpretation onto someone with zero technical context to bear it.

This requires concrete work. You need a separate translation layer between what the system knows and what the user sees. That layer answers three questions in every message: what happened, why it matters to you, what you do now.$p204$, brand, platform, topic, status, content_item_id, '2026-07-22 20:37+02', '[]'::jsonb
FROM post_queue WHERE id = 204;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p204$A 422 at that layer doesn't become less precise. It becomes two-layered. Full technical data stays in logs for debugging. The screen gets one sentence someone can actually use.

Architecture that skips this layer looks complete until someone hits an error. Then you see who built for machines and who built for humans using them.

Remember: error translation isn't polish at the end. It's part of the contract with the user, as binding as the business logic itself. #agentarchitecture$p204$, brand, platform, topic, status, content_item_id, '2026-07-22 21:19+02', '[]'::jsonb
FROM post_queue WHERE id = 204;

-- #221: 640 zn -> 2 czesci
UPDATE post_queue SET content = $p221$Saturday morning. Agent answers a customer's price question with perfect grammar and clean formatting.

Wrong number though.

Nobody caught it. The system didn't flag it. Logs looked clean because technically nothing broke. The model just confidently hallucinated, and the whole architecture treated it as a win because the API returned 200.

This is the scariest failure mode in agent systems: silent.$p221$ WHERE id = 221;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p221$Server didn't crash. No 500 error. The agent just told your customer something completely false at 200 milliseconds, no alarms fired, because traditional monitoring watches for technical failures, not for whether the answer makes sense.$p221$, brand, platform, topic, status, content_item_id, '2026-07-29 21:23+02', '[]'::jsonb
FROM post_queue WHERE id = 221;

-- #222: 746 zn -> 2 czesci
UPDATE post_queue SET content = $p222$Your agent can respond in milliseconds without errors and tell customers complete lies.

Classic observability catches what breaks visibly: latency, error codes, uptime. It doesn't catch whether the content is true. That requires a different layer entirely.

Three patterns that actually work:

Content validation before send (price, availability, personal data get a second gate: does this number exist in your actual database or did the model invent it).$p222$ WHERE id = 222;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p222$Confidence scoring as a signal, not a decision (low certainty on a critical answer routes to human or alternative, regardless of how well the sentence reads).

Random spot checks on high-risk categories (pricing, terms, sensitive data deserve regular human review before patterns spread).$p222$, brand, platform, topic, status, content_item_id, '2026-07-30 13:07+02', '[]'::jsonb
FROM post_queue WHERE id = 222;

-- #224: 2146 zn -> 6 czesci
UPDATE post_queue SET content = $p224$# X Adaptation

Someone asks in comments: "how much does one conversation with an agent cost?" The answer "a few cents per token" is technically true and practically useless.$p224$ WHERE id = 224;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p224$A conversation with an agent isn't one model call. It's usually several layers at once: a reasoning model that plans steps. A cheaper model that classifies intent. Embeddings to search a knowledge base. Sometimes audio transcription. Sometimes an external API call, which has its own pricing. Each layer has different per-token costs, different billing models (per token, per request, per minute), and sometimes isn't counted in tokens at all.$p224$, brand, platform, topic, status, content_item_id, '2026-07-30 17:29+02', '[]'::jsonb
FROM post_queue WHERE id = 224;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p224$Per-token cost of a single model tells you as much as fuel price tells you about the cost of driving a route. It doesn't account for consumption, traffic jams, or that part of the drive you take a taxi.$p224$, brand, platform, topic, status, content_item_id, '2026-07-30 18:43+02', '[]'::jsonb
FROM post_queue WHERE id = 224;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p224$The full bill from start to finish looks different. You count every call in the entire chain, not just the main model. You count retries, because an agent sometimes repeats a step when the response fails validation. You count context cost, which grows with each conversation turn because history goes into every next prompt. You count external tools separately, because their pricing lives its own life independent of LLM prices.$p224$, brand, platform, topic, status, content_item_id, '2026-07-30 19:57+02', '[]'::jsonb
FROM post_queue WHERE id = 224;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p224$This requires concrete work. You need to design cost logging at every step level, not just the full session. In practice that means tagging every call: which model, how many input and output tokens, was it a retry or main path. Without this you get one summary invoice at month end and zero answers to which part of the stack actually costs.

Only with that breakdown do you see where money really goes. Often it turns out you don't pay most for the reasoning model, but for context that unnecessarily grows, or for an external tool called more often than needed.$p224$, brand, platform, topic, status, content_item_id, '2026-07-31 13:26+02', '[]'::jsonb
FROM post_queue WHERE id = 224;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p224$So remember: "how much per token" is the wrong question from the start. The right question is: how much does one full conversation cost, counting every model, every API and every retry along the way. Only that number lets you design the stack consciously, instead of chasing a metric that says nothing about your actual bill.$p224$, brand, platform, topic, status, content_item_id, '2026-07-31 15:12+02', '[]'::jsonb
FROM post_queue WHERE id = 224;

-- #242: 1156 zn -> 3 czesci
UPDATE post_queue SET content = $p242$Builds agent for customer support tickets.

Starts in the wrong place.

First question isn't "can we build an agent". It's: does this problem actually need one, or just a script that does one thing well, the same way every time.

Clear start. Clear end. Zero decisions in between. Predictable inputs. No branching. That's script work. Input, transform, output. No autonomy required because there's nothing to autonomously decide.$p242$, scheduled_for = '2026-07-21 14:23+02' WHERE id = 242;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p242$Agent makes sense when the middle has forks. System reads context, picks one of several paths, maybe corrects itself if the first attempt fails. A support ticket that needs classification plus checks in three data sources plus a decision on next steps, that's not linear anymore. That's reasoning, not just execution.

Problem: agent sounds more modern than admitting a script would work. Looks better in the pitch. But an agent solving a script problem is just complexity you don't need. More costs. More failure points. More unknowns where you actually wanted predictability.$p242$, brand, platform, topic, status, content_item_id, '2026-07-21 16:41+02', '[]'::jsonb
FROM post_queue WHERE id = 242;
INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
SELECT $p242$Honestly, selling an agent when the architecture doesn't require it isn't quite fair to the client.

Design the process first. Then pick the tool.$p242$, brand, platform, topic, status, content_item_id, '2026-07-21 19:07+02', '[]'::jsonb
FROM post_queue WHERE id = 242;

-- Sprzatanie zdublowanej propozycji planu z crona nd 20:15 (plan tygodnia zatwierdzony recznie 14:57)
UPDATE content_items SET status='rejected', updated_at=NOW() WHERE brand_id='AGS' AND status='proposed';

-- Kontrola (oczekiwane: proposed=0, x_dlugie_bez_serii=0)
SELECT 'proposed' AS co, COUNT(*)::text AS n FROM content_items WHERE status='proposed'
UNION ALL SELECT 'x_dlugie_bez_serii', COUNT(*)::text FROM post_queue WHERE platform='x' AND status IN ('review','scheduled','queued') AND length(content) > 700
UNION ALL SELECT 'x_wierszy_w_kolejce', COUNT(*)::text FROM post_queue WHERE platform='x' AND status IN ('review','scheduled','queued');
COMMIT;
