-- Preserve source-photo thumbnails separately from AI-generated catalog depictions.
-- Each processing run retains its own generated preview path and generation audit JSON.
alter table public.bottle_processing_runs
  add column if not exists generated_thumbnail_path text,
  add column if not exists generation_json jsonb;
