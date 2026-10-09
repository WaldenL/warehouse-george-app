# Warehouse George AWS Lambda worker

Region: us-east-2. GitHub workflow: .github/workflows/deploy-lambda.yml (manual dispatch). ECR and Lambda: warehouse-george-worker. The runtime execution role is WarehouseGeorgeLambdaExecutionRole.

The handler takes JSON input: {"processing_run_id":"<UUID>"}. It expects a Lambda environment variable WAREHOUSE_WORKER_CONFIG containing JSON with SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY. Never commit keys to GitHub. Prefer AWS Secrets Manager before production; the initial environment variable is a deployment/testing bridge. Do not share key values in chat.

Each job claims a queued/retry_pending run, downloads immutable originals, resizes with Pillow, isolates background via the non-generative rembg model (falling back to resized original on error), stores working media and a 192x288 PNG thumbnail, extracts facts from working photographs via OpenAI, and writes result JSON and run metadata to Supabase.

IMPORTANT: The Lambda code is initial integration code, not production-verified. It currently uses a free-form JSON extraction prompt, rather than the strict warehouse_visual_v1_1 schema, and should not be considered equivalent to the existing extractor until that is migrated. The u2netp model download at cold start and the dependencies have not yet been runtime-benchmarked. The scheduled AWS dispatcher and lease-recovery logic are not enabled. Keep the Supabase scheduled worker disabled before any AWS jobs are dispatched and reconcile its previously stranded processing runs. Never run competing workers.

Required next validation: Docker build in GitHub Actions; Lambda existence; authenticated invocation; one existing test run from Supabase; extraction schema parity, image correctness, runtime memory/duration, retries, and no image overwrites.
