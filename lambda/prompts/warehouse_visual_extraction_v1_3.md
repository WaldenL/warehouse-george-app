Warehouse Visual Extraction v1.3. 

All photos show the SAME physical wine or spirits bottle. Integrate fragments across views. VISUAL evidence only: no research, no historical assumptions or valuation. Preserve original label wording separately from interpretations, with photo numbers in evidence and label_transcriptions. For each meaningful assertion use evidence entries with 1-based photo numbers.

Read brand, producer, expression, distillery/bottler/importer label text, origin; production/barreling/bottling/vintage/release dates; age, barrel, batch, cask, finish; ABV; volume; wine varieties/appellation; special releases, closures and condition. 

Extract the bottle's volume designation exactly as printed. Preserve the original units, fractions, terminology, and wording. Do not convert, normalize, infer units, or calculate an equivalent volume. 

If ABV is not present but proof is, ABV can be calculated as proof * 0.5. ABV must be numeric. Proof is only an input for calculating ABV; do not output proof as a separate structured attribute. 

A copyright, trademark, or other administrative date is not evidence of a distillation, bottling, vintage, or release date unless the label explicitly establishes that relationship. A number may be transcribed accurately even when its purpose cannot be determined. Do not assign it to a tax stamp, producer bottle number, or other identifier category without supporting visual context.

Separate tax stamps, excise strips, government markings, manufacturer codes, unknown printed numbers, and producer bottle numbers. Be conservative about fill, seal condition and label wear; if a capsule is visible it doesn't establish an intact seal.

Warehouse inventory sticker identification: Warehouse inventory stickers are small, rectangular silver stickers, approximately 0.39 × 0.78 inches, bearing exactly four black machine-printed digits and no other markings. They are physically separate from the manufacturer's labeling and may appear above, below, beside, or on the bottom of the bottle.
Only populate warehouse_label_number when a sticker matching these characteristics is clearly visible and the number can be read with high confidence. Never classify a number printed or handwritten on the manufacturer's labeling as a Warehouse sticker, regardless of its length. If the sticker's identity or number is uncertain, use null for warehouse_label_number and warehouse_sticker_confidence, and document the uncertainty.

Never introduce a number, name, date, or designation from these instructions into extracted facts unless visual inspection independently confirms it on the bottle. When visible text has an uncertain meaning, preserve it under an unclassified field rather than assigning an unsupported interpretation.

Return only JSON adhering to the supplied versioned schema. Empty, not seen, not visible, or unknown scalar fields must be null, empty arrays []; don't invent. A condition that cannot be assessed must be null rather than 'not visible', 'not seen', or a guessed condition. Only set a confidence value when an actual candidate Warehouse sticker is visible.