-- Preserve generated front and back catalog previews independently.
-- Existing generated_thumbnail_path remains the primary/front preview.
ALTER TABLE public.bottle_processing_runs
  ADD COLUMN IF NOT EXISTS generated_back_thumbnail_path text;
