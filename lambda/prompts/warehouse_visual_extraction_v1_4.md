Warehouse Visual Extraction 

All photos show the SAME physical wine or spirits bottle. Integrate fragments across views. VISUAL evidence only: no research, no historical assumptions or valuation. Preserve original label wording separately from interpretations, with photo numbers in evidence and label_transcriptions. For each meaningful assertion use evidence entries with 1-based photo numbers.

Read brand, producer, expression, distillery/bottler/importer label text, origin; production/barreling/bottling/vintage/release dates; age, barrel, batch, cask, finish; ABV/proof; volume; wine varieties/appellation; special releases, closures and condition. 

Extract the bottle's volume designation exactly as printed. Preserve the original units, fractions, terminology, and wording. Do not convert, normalize, infer units, or calculate an equivalent volume. 

If ABV is not present but proof is, ABV can be calculated as proof * 0.5. Proof/ABV must be numeric. 

A copyright, trademark, or other administrative date is not evidence of a distillation, bottling, vintage, or release date unless the label explicitly establishes that relationship. A number may be transcribed accurately even when its purpose cannot be determined. Do not assign it to a tax stamp, producer bottle number, or other identifier category without supporting visual context.

Separate tax stamps, excise strips, government markings, manufacturer codes, unknown printed numbers, and producer bottle numbers. Be conservative about fill, seal condition and label wear; if a capsule is visible it doesn't establish an intact seal.

Warehouse inventory sticker identification: Warehouse inventory stickers are small, rectangular silver stickers, approximately 0.39 × 0.78 inches, bearing exactly four black machine-printed digits and no other markings. They are physically separate from the manufacturer's labeling and may appear above, below, beside, or on the bottom of the bottle.
Only populate warehouse_label_number when a sticker matching these characteristics is clearly visible and the number can be read with high confidence. Never classify a number printed or handwritten on the manufacturer's labeling as a Warehouse sticker, regardless of its length. If the sticker's identity or number is uncertain, use null and document the uncertainty.

Ignore Government warning:
The text “GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.” Should be ignored, not documented, and not used to infer anything. 

Never introduce a number, name, date, or designation from these instructions into extracted facts unless visual inspection independently confirms it on the bottle. When visible text has an uncertain meaning, preserve it under an unclassified field rather than assigning an unsupported interpretation.

Return only JSON adhering to the supplied versioned schema. Empty/unknown scalar fields must be null, empty arrays []; don't invent.