-- CM seed for AGS (30/06/2026). Idempotent (ON CONFLICT DO NOTHING). Data only - Tomasz/Manager refine
-- brand_strategy + channel config later. Other brands (TNM, RDC, SdI) onboarded the same way per brand.

-- AGS tenant
INSERT INTO brands (brand_id, brand_name, status) VALUES
 ('AGS','Authentic Growth Systems','active')
ON CONFLICT (brand_id) DO NOTHING;

-- AGS strategy (defaults from brand canon; refine via Manager/Obsidian projection)
INSERT INTO brand_strategy (brand_id, target_audience, content_pillars, core_topics) VALUES
 ('AGS',
  'Founders and solo operators building real businesses with AI agents; technical-enough to value architecture over hype.',
  ARRAY['architecture','AI agents','founder operations'],
  ARRAY['agent orchestration','build-in-public','cost-aware AI','automation that ships'])
ON CONFLICT (brand_id) DO NOTHING;

-- AGS channels: X active (publish via post_queue + existing Scheduler), LinkedIn draft-only, rest ready-to-plug.
INSERT INTO channels (brand_id, channel, status, config) VALUES
 ('AGS','x',        'active', '{"publish_mode":"post_queue"}'::jsonb),
 ('AGS','linkedin', 'draft',  '{"publish_mode":"draft"}'::jsonb),
 ('AGS','youtube',  'ready',  '{"publish_mode":"webhook"}'::jsonb),
 ('AGS','facebook', 'ready',  '{"publish_mode":"webhook"}'::jsonb),
 ('AGS','instagram','ready',  '{"publish_mode":"webhook"}'::jsonb)
ON CONFLICT (brand_id, channel) DO NOTHING;

-- register the CM agent (network member; capped to low/medium per critical-restriction db/007)
INSERT INTO agent_registry (agent_name, agent_type, role, model_tier, status, current_gate, allowed_model_tiers) VALUES
 ('content-manager','specialist','Brand-aware content backbone (supervisor of channel subagents)',
  'sonnet-4-6','building','awaiting_acceptance', ARRAY['low','medium'])
ON CONFLICT (agent_name) DO NOTHING;
