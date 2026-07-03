-- CM Brain Faza 1 krok 1f (03/07/2026, ags_crd). Idempotent. Wymaga rozszerzenia vector (LIVE 0.8.2 od 23/06).
-- Embeddingi archiwum publikacji (find_similar / reuse cross-channel): OpenAI text-embedding-3-small (1536).
ALTER TABLE published_posts ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- hook nowego kanalu: istniejace aktywne kanaly oznaczamy jako powitane, zeby propozycja adaptacji
-- odpalala sie tylko dla KANALOW AKTYWOWANYCH W PRZYSZLOSCI (np. Instagram)
UPDATE channels SET config = config || '{"welcomed": true}'::jsonb WHERE status IN ('active','draft');
