Warehouse Visual Extraction — evidence-backed observations

All photos show the SAME physical wine or spirits bottle. Integrate fragments across views. VISUAL evidence only: no research, no historical assumptions or valuation. Preserve original label wording in label_transcriptions. Return identified facts as a flat observations array, not grouped or nested attributes. Each observation MUST contain its field name, literal value, 1-based source photo numbers, an exact supporting visible text excerpt (or a concise visual description for condition), and basis. Never report a fact in transcriptions or observations without putting the corresponding supported value in the observation for that field. No separate evidence list; the evidence belongs to the fact.

Read brand, producer, expression, distillery/bottler/importer label text, origin; production/barreling/bottling/vintage/release dates; age, barrel, batch, cask, finish; ABV/proof; volume; wine varieties/appellation; special releases, closures and condition. 

Extract the bottle's volume designation exactly as printed. Preserve the original units, fractions, terminology, and wording. Do not convert, normalize, infer units, or calculate an equivalent volume. 

If ABV is not present but proof is, ABV can be calculated as proof * 0.5. Return ABV as the abv_percent observation; do not create a proof observation. Values are strings (e.g. 65.8). For calculated values use basis calculation and quote the proof on the source photograph in evidence_text. 

A copyright, trademark, or other administrative date is not evidence of a distillation, bottling, vintage, or release date unless the label explicitly establishes that relationship. A number may be transcribed accurately even when its purpose cannot be determined. Do not assign it to a tax stamp, producer bottle number, or other identifier category without supporting visual context.

Separate tax stamps, excise strips, government markings, manufacturer codes, unknown printed numbers, and producer bottle numbers. Be conservative about fill, seal condition and label wear; if a capsule is visible it doesn't establish an intact seal.

Warehouse inventory sticker identification: Warehouse inventory stickers are small, rectangular silver stickers, approximately 0.39 × 0.78 inches, bearing exactly four black machine-printed digits and no other markings. They are physically separate from the manufacturer's labeling and may appear above, below, beside, or on the bottom of the bottle.
Only emit a warehouse_label_number observation when a sticker matching these characteristics is clearly visible and the number can be read with high confidence. Never classify a number printed or handwritten on the manufacturer's labeling as a Warehouse sticker, regardless of its length. If the sticker's identity or number is uncertain, omit that observation and document the uncertainty.

Ignore Government warning:
The text “GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.” Should be ignored, not documented, and not used to infer anything. 

Never introduce a number, name, date, or designation from these instructions into extracted facts unless visual inspection independently confirms it on the bottle. When visible text has an uncertain meaning, preserve it under an unclassified field rather than assigning an unsupported interpretation.

Return only JSON adhering to the supplied schema. Omit unobserved facts entirely: no null observations, no placeholders, no not_seen/not_visible/unknown values. Arrays may be empty. Do not invent, duplicate fields, or promote administrative dates to production dates. Treat ambiguous numbers as unclassified_numbers and preserve their literal text. A clearly labeled 'Barrel No.' must produce a barrel_number observation with the same numeral and photograph reference; never leave it only in a transcription. Ignore the standard government health warning entirely, including in label_transcriptions.

## Thumbnail brief (planning only — no image generation)
Return a top-level `thumbnail_brief` describing how a later OpenAI image-generation step should depict THIS exact physical bottle, using the supplied photographs as the authoritative visual references. This brief is not a verified inventory fact and must not contaminate the observations.

- `strategy`: `label_forward` when labels distinguish this bottle most, `shape_forward` when its silhouette is most distinctive, otherwise `balanced`.
- `canonical_photo_numbers`: 1-based references to the best one or more photographs for generating an accurate representative thumbnail. Reference only photographs supplied in this pass.
- `show_full_bottle`: ordinarily true; use false only when a close detail is more recognizable.
- `tight_crop`: whether a close frame is helpful while retaining the intended visual context.
- `identity_anchors`: concise, visually verified features that MUST be preserved, including distinctive shape, label design and legible identity-critical text, capsule, markings, and liquid level where applicable. Never invent label text.
- `optional_anchors`: secondary visible features worth retaining if possible.
- `simplifications_allowed`: fine print or microdetails that may be simplified for thumbnail readability; never authorize substitution of a generic or fictitious bottle.
- `notes`: optional short depiction instruction relevant to this particular bottle, or null.

Aim for faithful recognizability of the actual bottle, not generic attractiveness. Studio lighting and a clean subtle neutral background can be applied later by a fixed house style prompt, so do not ask for unrelated scenery or stylistic embellishment. The thumbnail brief is a separate planning artifact; do not use it as independent evidence for extraction fields.
