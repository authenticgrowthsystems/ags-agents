-- INCYDENT PUBLIKACJI 20/07 (burst + PL na kanalach EN + zgubione grafiki) - NAPRAWA.
-- Root cause: publish_mode='webhook' (delegat publikuje natychmiast, ignoruje sloty pq,
-- callback oznacza WSZYSTKIE wiersze materialu jako published, gubi media wierszy).
-- Sonda 20/07 ~22:15: wszystkie wiersze incydentu = 'review', materialy 'approved'
-- z przyszlymi slotami (21/07 13:15, 23/07 16:00, 23/07 18:45); zero held/scheduled.
-- Dispatch przy slocie materialu przelaczy review -> scheduled, Scheduler opublikuje
-- kazdy wiersz w jego slocie. Zadnego freeze nie trzeba - transakcja jest atomowa.
BEGIN;
-- 1) tryby publikacji: X wraca na Scheduler (sloty+media), LinkedIn na gotowce reczne
UPDATE channels SET config = jsonb_set(config, '{publish_mode}', '"post_queue"') WHERE brand_id='AGS' AND channel='x';
UPDATE channels SET config = jsonb_set(config, '{publish_mode}', '"draft"') WHERE brand_id='AGS' AND channel='linkedin';
-- 2) re-slot wierszy ze slotami z 19/07 (material dispatchuje sie 23/07 18:45 -
--    sloty wierszy MUSZA byc pozniejsze, inaczej Scheduler strzeli od razu)
UPDATE post_queue SET scheduled_for='2026-07-23 19:12+02' WHERE id=246;
UPDATE post_queue SET scheduled_for='2026-07-23 20:23+02' WHERE id=247;
UPDATE post_queue SET scheduled_for='2026-07-24 17:42+02' WHERE id=248;
-- 3) tlumaczenia EN (karta kontrolna: docs/ops/TLUMACZENIA_EN_20072026.md)
UPDATE post_queue SET content = $en182$Four intents worked without a hitch. The fifth answers a complaint question with pricing info. No log flags an error. The system appears to work. It doesn't.$en182$ WHERE id = 182;
UPDATE post_queue SET content = $en183$An intent classifier at 90% accuracy with four categories has no guarantee of holding that level with five. The boundaries between intents blur. The model no longer decides just "is this a pricing question" but "is this a pricing question, or something that sounds like one and isn't". Without a routing layer, that is a change to the decision boundaries of the whole system. Nobody calls it that, though.$en183$ WHERE id = 183;
UPDATE post_queue SET content = $en184$The routing layer is its own place: a threshold below which the bot asks instead of guessing, a fallback when nothing fits, a decision about who takes over (a human or a module). That takes concrete work, before the number of intents grows to the point where silent failure becomes the norm.$en184$ WHERE id = 184;
UPDATE post_queue SET content = $en185$Four intents forgive missing architecture. The fifth doesn't. The sixth will make it even clearer. Adding another feature to a bot is a good moment to ask: does the system even know when it doesn't know.$en185$ WHERE id = 185;
UPDATE post_queue SET content = $en210$Saturday afternoon. Someone builds an agent to classify five hundred support tickets and picks the most expensive model available. The reasoning: "better model, better result". Two days earlier the same person used the same model for a one-sentence summary in a report. Both choices are wrong. For different reasons.$en210$ WHERE id = 210;
UPDATE post_queue SET content = $en211$Cost per task is not an accounting detail. It's an input to an architectural decision, same as latency or availability. Postponing it ("we'll optimize costs later") is a signal the architecture was built without a plan.$en211$ WHERE id = 211;
UPDATE post_queue SET content = $en212$Classifying five hundred tickets: high frequency, low cost of error (the ticket lands with a human who corrects it). A cheaper model is enough. Summarizing a contract: low frequency, high cost of error (reputation, legal risk, time to repair). There the pricier model is an investment, not an expense.$en212$ WHERE id = 212;
UPDATE post_queue SET content = $en213$You need a task matrix. X axis: frequency. Y axis: cost of error. High frequency and low error cost gets the cheap model automatically. Low frequency and high error cost gets the expensive model, no debate. Real architecture lives in the middle of the matrix.$en213$ WHERE id = 213;
UPDATE post_queue SET content = $en214$Conditional routing: a cheap model as the filter, escalation to a pricier one when confidence drops below a threshold or when the task carries high-risk markers (transaction amount, legal wording, negative sentiment). That's not a compromise. That's architecture that invests in quality exactly where quality matters.$en214$ WHERE id = 214;
UPDATE post_queue SET content = $en215$One model for everything looks like the simpler decision. It's just more expensive at scale and less accurate where accuracy matters. Cost per task deserves the same attention as your choice of tools or your database schema.$en215$ WHERE id = 215;
-- 4) bezpiecznik: gdyby KROK 1 (hold) zostal jednak wykonany wczesniej - odmrozenie;
--    UWAGA: nie rusza 3 wierszy linkedin/review (te po zmianie trybu obsluzy dispatch jako gotowce)
UPDATE post_queue SET status='review' WHERE status='held';
-- 5) kontrola (oczekiwane: pl_na_kanalach_en=0, held=0, tryby: x=post_queue, linkedin=draft)
SELECT 'pl_na_kanalach_en' AS co, COUNT(*)::text AS n FROM post_queue WHERE status IN ('review','scheduled') AND content ~ '[ąćęłńóśźż]'
UNION ALL SELECT 'held', COUNT(*)::text FROM post_queue WHERE status='held'
UNION ALL SELECT ch.channel, ch.config->>'publish_mode' FROM channels ch WHERE ch.brand_id='AGS' AND ch.channel IN ('x','linkedin');
COMMIT;
