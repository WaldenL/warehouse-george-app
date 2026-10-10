-- One-time, idempotent backfill of the actual image API usage on legacy one-view runs.
-- Pricing: standard API, USD per million tokens as of 2026-10-10.
WITH historical AS (
 SELECT id,
        ROUND(((generation_json->'usage'->'input_tokens_details'->>'text_tokens')::numeric*5
              +(generation_json->'usage'->'input_tokens_details'->>'image_tokens')::numeric*8
              +(generation_json->'usage'->'output_tokens_details'->>'image_tokens')::numeric*30)/1000000,8) image_usd,
        (cost_json->>'estimated_total_usd')::numeric extraction_usd,
        generation_json->'usage'->'input_tokens_details' AS inputs,
        generation_json->'usage'->'output_tokens_details' AS outputs
 FROM public.bottle_processing_runs
 WHERE generation_json->>'status'='completed'
   AND generation_json->'cost_json' IS NULL
   AND generation_json->'usage'->'input_tokens_details'->>'text_tokens' IS NOT NULL
   AND generation_json->'usage'->'input_tokens_details'->>'image_tokens' IS NOT NULL
   AND generation_json->'usage'->'output_tokens_details'->>'image_tokens' IS NOT NULL
)
UPDATE public.bottle_processing_runs r
SET generation_json=jsonb_set(r.generation_json,'{cost_json}',
       jsonb_build_object('status','estimated','type','estimate','currency','USD',
          'estimated_total_usd',h.image_usd,'pricing_date','2026-10-10',
          'pricing_source','https://platform.openai.com/pricing/',
          'model',r.generation_json->>'model',
          'rates_usd_per_million_tokens',jsonb_build_object('text_input',5,'image_input',8,'image_output',30),
          'token_breakdown',jsonb_build_object('text_input',(h.inputs->>'text_tokens')::integer,
               'image_input',(h.inputs->>'image_tokens')::integer,
               'image_output',(h.outputs->>'image_tokens')::integer)),true),
    cost_json=COALESCE(r.cost_json,'{}'::jsonb)||jsonb_build_object(
       'extraction_estimated_usd',h.extraction_usd,
       'front_image_estimated_usd',h.image_usd,
       'image_generation_estimated_usd',h.image_usd,
       'image_generation_known_estimated_usd',h.image_usd,
       'combined_estimated_total_usd',CASE WHEN h.extraction_usd IS NULL THEN NULL ELSE h.extraction_usd+h.image_usd END,
       'estimation_status','complete',
       'image_pricing',jsonb_build_object('model',r.generation_json->>'model',
          'pricing_date','2026-10-10','pricing_source','https://platform.openai.com/pricing/',
          'rates_usd_per_million_tokens',jsonb_build_object('text_input',5,'image_input',8,'image_output',30)))
FROM historical h WHERE r.id=h.id;
