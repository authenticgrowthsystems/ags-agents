# Prompty badawcze: Agent Wizualny (10/07/2026)

Do recznego uruchomienia przez Tomasza (ChatGPT Deep Research / Gemini Deep Research / Manus).
Zalecenie: prompt 1 i 2 w DWOCH roznych narzedziach (krzyzowa weryfikacja zrodel).
Raporty wracaja do BE -> selekcja 2-3 adapterow startowych + kosztorys (SPEC_VISUAL_AGENT_10072026.md).

---

## PROMPT 1 - modele GRAFIKI (image generation APIs)

I am building an autonomous "Visual Agent" microservice (Python FastAPI on a small Linux VPS)
that generates ON-BRAND social media graphics via APIs (no browser automation, server-side
API calls only). Research the current landscape (as of mid-2026) of image generation APIs
and give me a decision-ready comparison.

Models/providers to cover (verify exact current names and versions, add any I missed):
OpenAI gpt-image, ByteDance Seedream (what is the latest version? is "Seedream 2.0" or
"Seedance" the image model?), Black Forest Labs Flux family (including reference/context
variants), Google Imagen, Ideogram, Recraft, Stability AI, Midjourney (is there an official
API now?), Adobe Firefly Services.

For EACH, report:
1. API availability for server-side use (official API, pricing page, rate limits, EU access).
2. Price per image at ~1536x1024 / high quality.
3. TEXT RENDERING accuracy on graphics (headlines must be letter-perfect - which models are
   best at typography?).
4. REFERENCE IMAGE support: can I pass brand logo images, style references, or photos of a
   real person (the founder) to keep consistency across generations? What are the policies
   and safety restrictions on real faces?
5. BRAND COLOR fidelity: can it follow exact hex colors and a fixed 4-5 color palette reliably?
6. Commercial license terms for generated images (social media marketing use).
7. Latency and reliability (sync vs async job API).

Finish with: a ranked TOP 3 for my use case (typographic/diagram-style brand graphics with
exact palette + occasional illustrations), with one-paragraph justification each, and a table
of all models vs criteria. Cite sources with dates.

---

## PROMPT 2 - modele WIDEO (video generation APIs)

I am building an autonomous "Visual Agent" microservice (Python FastAPI on a Linux VPS) that
must also generate SHORT SOCIAL VIDEOS (5-15 seconds, 16:9 and 9:16) for X/Twitter and
LinkedIn via server-side APIs. Research the current landscape (as of mid-2026) of video
generation APIs and give me a decision-ready comparison.

Models/providers to cover (verify exact current names/versions, add any I missed):
ByteDance Seedance, Google Veo, Kling (Kuaishou), Runway, Luma Dream Machine, Pika,
OpenAI Sora (API status?), Minimax/Hailuo, Alibaba Wan.

For EACH, report:
1. Official API availability for server-side automation (not just a web app), EU access.
2. Price per second of generated video / per clip; typical generation time.
3. Modes: text-to-video, image-to-video (animating a brand graphic we already have),
   reference-based character consistency.
4. Max length, resolution, aspect ratios (16:9, 9:16, 1:1).
5. Text/typography rendering in video (can it show a headline without garbling letters?).
6. Policies on real people's faces (founder photos as reference) and commercial use license.
7. Reliability: async job APIs, webhooks, queue times.

Finish with: a ranked TOP 3 for short branded social clips (product/build-in-public content,
occasional talking-head-free explainers), one-paragraph justification each, full comparison
table, sources with dates.

---

## PROMPT 3 - spojnosc brandu w generacji (pipeline best practices)

Research question: what is the state of the art (mid-2026) for keeping AI-generated marketing
visuals STRICTLY ON-BRAND (exact hex palette, specific fonts like Playfair Display / DM Sans /
JetBrains Mono, logo placement, consistent style across hundreds of images)?

Compare these approaches with real-world evidence (case studies, engineering blogs, docs):
1. Prompt-only brand control (detailed prompts with hex codes) - how reliable is it really?
2. Reference images / style references passed to the model per request.
3. Fine-tuning / LoRA / custom style models - which providers offer this via API, cost,
   effort, and is it worth it for a solo operator?
4. Template/code rendering: generating SVG or HTML/CSS with exact fonts and colors and
   rendering to PNG server-side (tools like resvg, headless chromium) - when do teams choose
   this over diffusion models?
5. Canva Connect API: can brand-template autofill be automated server-side, on which Canva
   plan, at what cost, and what are its limits vs the approaches above?
6. Consistent founder-face generation from reference photos: which providers allow it, what
   verification/safety hoops exist, and what do practitioners actually use in 2026?

Finish with: a recommended HYBRID architecture for a solo-operator content system (which
approach for typographic graphics, which for illustrations, which for photos with the
founder's face, which for video), with estimated monthly cost at ~100 graphics + ~10 videos
per month. Cite sources with dates.
