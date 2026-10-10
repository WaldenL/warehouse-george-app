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

## Front/back catalog image brief (planning only — no image generation)
Produce the top-level `thumbnail_brief` so that a later OpenAI image generator can faithfully depict THIS particular physical bottle from the reference photos. The objective is recognition of the actual bottle, not catalog completeness, factual extraction, generic brand recognition, or merely a pretty image.

Before choosing anchors, assess ALL supplied photographs together for visual distinctiveness:
1. Silhouette, proportions, glass color, closure, capsule color and unusual shape.
2. Primary label design: geometry, color, artwork, typography, prominent text, placement.
3. Secondary features: neck labels, bespoke selection names, markings, handwritten identifiers, stickers, seals, numbered editions.
4. Contents and condition: visible liquid color and distinctive fill level when relevant to faithful depiction.
5. Which traits separate this bottle from others of the SAME brand or expression?

Choose approximately 4–8 concrete `identity_anchors` supported by the photos. These are MUST-preserve visual traits: prioritize things that are distinctive, conspicuous, or would make a generated depiction look like the wrong bottle if omitted or changed. Do not automatically prioritize brand, producer, spirit category, proof, ABV, or technical production fields simply because they are easy to extract. Do not automatically prioritize handwriting either: judge its visual significance. Include both recognition traits (distinctive markings, labels, silhouette) and faithfulness traits (proportions, dominant colors, fill level). Describe WHAT THE GENERATOR MUST SHOW, not schema or database field names. For instance, specify the actual shape, color, relative location, design, or verified lettering rather than writing `closure_description` or `abv_percent`.

Use `optional_anchors` for genuinely secondary features whose absence would not impair recognition. Use `simplifications_allowed` ONLY for real visual details that are safely simplified at thumbnail size, such as microscopic legal print or intricate hairline ornamentation. Never put database field names in `simplifications_allowed`.

Choose `strategy` as `label_forward`, `shape_forward`, or `balanced` according to which visual features best distinguish THIS bottle, not which facts are easy to read. Choose `canonical_photo_numbers` from the actual 1-based photo sequence: prefer the clearest image of its recognizably distinctive presentation, and include supplementary views whenever they uniquely establish critical features. Set `show_full_bottle` and `tight_crop` according to faithful recognition at small size (normally show the whole bottle). In `notes`, add only bottle-specific depiction guidance, or null. The later generator will apply a consistent restrained studio style; do not ask for irrelevant decoration or a fictitious redesign.

Before returning, CHECK the brief internally: Could this depict a generic same-brand bottle? Did you omit a notable capsule, neck label, special graphic, handwritten selection marking, fill level, or shape? Did you overemphasize technical data rather than visual identity? Would a collector recognize this specific bottle when the result is small? Revise the anchors if too generic. Do not generate the thumbnail now. The brief is NOT independent evidence for inventory observations.


### Two distinct, evidence-grounded catalog views
Plan two SEPARATE images: `front` (the most identifying main display face of the bottle) and `back` (the physically opposite label or reverse face). These are two depictions of the same physical bottle, not two different bottles. The main front is the face most useful to identify THIS particular bottle in a collection; when the brand's standard face is less distinctive than a private-selection or custom front label, favor the uniquely identifying face as the catalog front. The back must depict the opposite face, never another angle of the same front.

Populate `front_photo_numbers` with 1-based numbers of photographs that actually show the chosen front face; use the clearest as the first entry, optionally adding other photos of that SAME face. Populate `back_photo_numbers` ONLY when at least one supplied photograph visibly shows the opposite/reverse face; use the clearest as the first entry. A side-angle, neck close-up, duplicate front, or guess that every bottle has a rear label is NOT evidence of a back view. If the back is not photographed, set `back_photo_numbers` to [] and `back_identity_anchors` to [], with `back_notes` explaining that no supported rear view exists. NEVER infer, invent, mirror, or synthesize an unseen back.

Describe concrete front-specific visual features in `front_identity_anchors`, and back-specific features in `back_identity_anchors`; these supplement shared `identity_anchors`. Distinguish different labels, inscriptions, and condition on each side. Keep front and back photo sets disjoint. Put viewpoint-specific depiction guidance in `front_notes` and `back_notes`, or null. `canonical_photo_numbers` should list the chosen front reference photographs for legacy display and compatibility. Always provide at least one front photo when any usable bottle photograph exists.

For each face, prioritize accurate shape, closure, glass, fill level, label positioning, typography and distinctive markings, without transplanting an opposite-face label onto it. The downstream generator receives ONLY photographs of the selected face for that request; it must not invent the unphotographed side.
