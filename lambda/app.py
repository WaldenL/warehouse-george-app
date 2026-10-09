import os, json, io, uuid, re, traceback
from datetime import datetime, timezone
import requests
from PIL import Image, ImageOps
from rembg import remove, new_session

TIMEOUT=40
EXTRACTION_PROMPT="Warehouse Visual Extraction v1.1. All photos show the SAME physical wine or spirits bottle. Integrate label fragments across views. VISUAL evidence only: no research, no historical assumptions or valuation. Read brand, producer, expression, distillery/bottler/importer label text, origin; production/barreling/bottling/vintage/release dates; age, barrel, batch, cask, finish; proof, ABV and volume; wine varieties/appellation; special releases, closures and condition. Preserve original label wording separately from interpretations, with photo numbers in evidence and label_transcriptions. Never classify a 4- or 5-digit number as a Warehouse sticker from digit count alone. In particular 8908 is NOT a Warehouse inventory sticker. Only populate warehouse_label_number if a physically distinct, clearly modern inventory sticker is identifiable with high confidence; if in doubt use null, confidence low/not_seen, and list number under unclassified_numbers or tax_stamp_numbers as applicable. Separate tax stamps, excise strips, government markings, manufacturer codes, unknown printed numbers, and producer bottle numbers. A producer-assigned number such as 50/56 belongs in producer_bottle_number. If uncertain leave meaning unclassified. Treat Traveler Fifth as a packaging or expression designation (identity.packaging_designation), NOT marketing language. Preserve the literal designation; do not assume it is a different whiskey recipe. Treat \"Rare Release\" as a label claim, not demonstrated scarcity; ordinary marketing claims are not private selections. Proof/ABV must be numeric, with printed/calculated/unknown source. Preserve labelled 4/5 quart exactly as volume_label_text. 4/5 US quart is approximately 757 mL, NOT 946 mL. Other conversions may be left null when ambiguous. Stated age distinct from inferred age. Empty/unknown scalar fields must be null, empty arrays []; don't invent. For each meaningful assertion use evidence entries with 1-based photo numbers. Be conservative about fill, seal condition and label wear; if a capsule is visible it doesn't establish an intact seal. Return only JSON adhering to the supplied versioned schema."
EXTRACTION_SCHEMA=json.loads("{\"type\":\"object\",\"additionalProperties\":false,\"required\":[\"schema_version\",\"identity\",\"production\",\"specification\",\"identifiers\",\"special_features\",\"condition\",\"label_transcriptions\",\"evidence\",\"uncertainties\"],\"properties\":{\"schema_version\":{\"type\":\"string\",\"enum\":[\"warehouse_visual_v1_1\"]},\"identity\":{\"type\":\"object\",\"additionalProperties\":false,\"required\":[\"brand\",\"expression\",\"packaging_designation\",\"category\",\"subcategory\",\"country\",\"region\",\"producer_label_text\"],\"properties\":{\"brand\":{\"type\":[\"string\",\"null\"]},\"expression\":{\"type\":[\"string\",\"null\"]},\"packaging_designation\":{\"type\":[\"string\",\"null\"]},\"category\":{\"type\":[\"string\",\"null\"]},\"subcategory\":{\"type\":[\"string\",\"null\"]},\"country\":{\"type\":[\"string\",\"null\"]},\"region\":{\"type\":[\"string\",\"null\"]},\"producer_label_text\":{\"type\":[\"string\",\"null\"]}}},\"production\":{\"type\":\"object\",\"additionalProperties\":false,\"required\":[\"distillery_label_text\",\"bottler_label_text\",\"importer_label_text\",\"distilled_and_bottled_by_label_text\",\"distilled_year\",\"barreled_year\",\"bottled_year\",\"vintage_year\",\"release_year\",\"stated_age_years\",\"stated_age_text\",\"barrel_number\",\"batch_number\",\"cask_type\",\"finish\"],\"properties\":{\"distillery_label_text\":{\"type\":[\"string\",\"null\"]},\"bottler_label_text\":{\"type\":[\"string\",\"null\"]},\"importer_label_text\":{\"type\":[\"string\",\"null\"]},\"distilled_and_bottled_by_label_text\":{\"type\":[\"string\",\"null\"]},\"distilled_year\":{\"type\":[\"integer\",\"null\"]},\"barreled_year\":{\"type\":[\"integer\",\"null\"]},\"bottled_year\":{\"type\":[\"integer\",\"null\"]},\"vintage_year\":{\"type\":[\"integer\",\"null\"]},\"release_year\":{\"type\":[\"integer\",\"null\"]},\"stated_age_years\":{\"type\":[\"number\",\"null\"]},\"stated_age_text\":{\"type\":[\"string\",\"null\"]},\"barrel_number\":{\"type\":[\"string\",\"null\"]},\"batch_number\":{\"type\":[\"string\",\"null\"]},\"cask_type\":{\"type\":[\"string\",\"null\"]},\"finish\":{\"type\":[\"string\",\"null\"]}}},\"specification\":{\"type\":\"object\",\"additionalProperties\":false,\"required\":[\"proof\",\"proof_source\",\"abv_percent\",\"abv_source\",\"volume_ml\",\"volume_label_text\",\"bottled_in_bond\",\"grape_varieties\",\"appellation\",\"other_specifications\"],\"properties\":{\"proof\":{\"type\":[\"number\",\"null\"]},\"proof_source\":{\"type\":\"string\",\"enum\":[\"printed\",\"calculated\",\"unknown\"]},\"abv_percent\":{\"type\":[\"number\",\"null\"]},\"abv_source\":{\"type\":\"string\",\"enum\":[\"printed\",\"calculated\",\"unknown\"]},\"volume_ml\":{\"type\":[\"number\",\"null\"]},\"volume_label_text\":{\"type\":[\"string\",\"null\"]},\"bottled_in_bond\":{\"type\":[\"boolean\",\"null\"]},\"grape_varieties\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"appellation\":{\"type\":[\"string\",\"null\"]},\"other_specifications\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}}},\"identifiers\":{\"type\":\"object\",\"additionalProperties\":false,\"required\":[\"warehouse_label_number\",\"warehouse_sticker_confidence\",\"producer_bottle_number\",\"tax_stamp_numbers\",\"government_markings\",\"manufacturer_codes\",\"unclassified_numbers\"],\"properties\":{\"warehouse_label_number\":{\"type\":[\"integer\",\"null\"]},\"warehouse_sticker_confidence\":{\"type\":\"string\",\"enum\":[\"high\",\"medium\",\"low\",\"not_seen\"]},\"producer_bottle_number\":{\"type\":[\"string\",\"null\"]},\"tax_stamp_numbers\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"government_markings\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"manufacturer_codes\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"unclassified_numbers\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}}},\"special_features\":{\"type\":\"object\",\"additionalProperties\":false,\"required\":[\"private_selection_name\",\"private_selection_label_text\",\"limited_release_label_claim\",\"other_label_claims\",\"distinctive_features\"],\"properties\":{\"private_selection_name\":{\"type\":[\"string\",\"null\"]},\"private_selection_label_text\":{\"type\":[\"string\",\"null\"]},\"limited_release_label_claim\":{\"type\":[\"string\",\"null\"]},\"other_label_claims\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"distinctive_features\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}}},\"condition\":{\"type\":\"object\",\"additionalProperties\":false,\"required\":[\"fill_level_description\",\"seal_status\",\"closure_description\",\"label_condition\",\"glass_condition\",\"packaging_condition\",\"condition_uncertainties\"],\"properties\":{\"fill_level_description\":{\"type\":[\"string\",\"null\"]},\"seal_status\":{\"type\":\"string\",\"enum\":[\"intact\",\"damaged\",\"opened\",\"uncertain\",\"not_visible\"]},\"closure_description\":{\"type\":[\"string\",\"null\"]},\"label_condition\":{\"type\":[\"string\",\"null\"]},\"glass_condition\":{\"type\":[\"string\",\"null\"]},\"packaging_condition\":{\"type\":[\"string\",\"null\"]},\"condition_uncertainties\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}}},\"label_transcriptions\":{\"type\":\"array\",\"items\":{\"type\":\"object\",\"additionalProperties\":false,\"required\":[\"photo_number\",\"text\",\"notes\"],\"properties\":{\"photo_number\":{\"type\":[\"integer\",\"null\"]},\"text\":{\"type\":\"string\"},\"notes\":{\"type\":[\"string\",\"null\"]}}}},\"evidence\":{\"type\":\"array\",\"items\":{\"type\":\"object\",\"additionalProperties\":false,\"required\":[\"field\",\"value\",\"photos\",\"basis\"],\"properties\":{\"field\":{\"type\":\"string\"},\"value\":{\"type\":\"string\"},\"photos\":{\"type\":\"array\",\"items\":{\"type\":\"integer\"}},\"basis\":{\"type\":\"string\",\"enum\":[\"visible_text\",\"visual_observation\",\"inference\"]}}}},\"uncertainties\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}}}")
def now(): return datetime.now(timezone.utc).isoformat()
def secret():
    value=os.environ.get("WAREHOUSE_WORKER_CONFIG","")
    if not value: raise RuntimeError("Missing WAREHOUSE_WORKER_CONFIG runtime secret")
    d=json.loads(value)
    for key in ("SUPABASE_URL","SUPABASE_SERVICE_ROLE_KEY","OPENAI_API_KEY"):
        if not d.get(key): raise RuntimeError("Missing secret field: "+key)
    return d
def api(cfg,method,path,payload=None,params=None):
    url=cfg["SUPABASE_URL"].rstrip("/")+"/rest/v1/"+path
    headers={"apikey":cfg["SUPABASE_SERVICE_ROLE_KEY"],"Authorization":"Bearer "+cfg["SUPABASE_SERVICE_ROLE_KEY"],"Content-Type":"application/json","Prefer":"return=representation"}
    r=requests.request(method,url,headers=headers,json=payload,params=params,timeout=TIMEOUT)
    r.raise_for_status();return r.json() if r.content else []
def storage(cfg,method,bucket,path,body=None,mime=None):
    base=cfg["SUPABASE_URL"].rstrip("/")+"/storage/v1/object/"
    headers={"apikey":cfg["SUPABASE_SERVICE_ROLE_KEY"],"Authorization":"Bearer "+cfg["SUPABASE_SERVICE_ROLE_KEY"]}
    if mime: headers.update({"Content-Type":mime,"x-upsert":"false","cache-control":"max-age=31536000, immutable" if mime.startswith("image/") else "no-cache"})
    endpoint=base+("authenticated/" if method=="GET" else "")+bucket+"/"+path
    r=requests.request(method,endpoint,headers=headers,data=body,timeout=120)
    if not r.ok: raise RuntimeError("Storage "+method+" failed ("+str(r.status_code)+"): "+r.text[:300])
    return r.content
def prep(cfg,run,media,session):
    bid=run["bottle_id"];rid=run["id"]; mid=media["id"]
    raw=storage(cfg,"GET","warehouse-media",media["object_path"])
    photo=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    photo.thumbnail((2200,2200),Image.Resampling.LANCZOS)
    # Segmentation is non-generative: the original RGB pixels are retained.
    # On failure, retain the photograph with its background and continue extraction.
    try:
        cut=remove(photo,session=session)
        rgba=cut.convert("RGBA")
        backdrop=Image.new("RGBA",rgba.size,(255,255,255,255))
        backdrop.alpha_composite(rgba);working=backdrop.convert("RGB")
        segment="completed"
    except Exception as exc:
        print(json.dumps({"stage":"segmentation","media_id":mid,"warning":str(exc)[:300]}))
        working=photo;segment="fallback"
    out=io.BytesIO();working.save(out,"JPEG",quality=90,optimize=True)
    path=f"bottles/{bid}/working/{rid}/{mid}.jpg"
    storage(cfg,"POST","warehouse-media",path,out.getvalue(),"image/jpeg")
    api(cfg,"PATCH","media",{"working_path":path,"working_mime_type":"image/jpeg"},params={"id":"eq."+mid})
    return path,working,segment
def thumbnail(cfg,run,im):
    thumb=Image.new("RGB",(192,288),"white")
    im=im.copy();im.thumbnail((184,280),Image.Resampling.LANCZOS)
    thumb.paste(im,((192-im.width)//2,(288-im.height)//2))
    out=io.BytesIO();thumb.save(out,"PNG")
    path=f"bottles/{run['bottle_id']}/{uuid.uuid4()}.png"
    storage(cfg,"POST","warehouse-thumbnails",path,out.getvalue(),"image/png")
    return path
def extract(cfg,run,paths):
    import base64
    content=[{"type":"input_text","text":EXTRACTION_PROMPT}]
    for i,path in enumerate(paths):
        b=storage(cfg,"GET","warehouse-media",path)
        content.extend([{"type":"input_text","text":f"Working photo {i+1}"},{"type":"input_image","image_url":"data:image/jpeg;base64,"+base64.b64encode(b).decode(),"detail":"high"}])
    response=requests.post("https://api.openai.com/v1/responses",headers={"Authorization":"Bearer "+cfg["OPENAI_API_KEY"],"Content-Type":"application/json"},json={"model":"gpt-4.1-mini","store":False,"max_output_tokens":3500,"text":{"format":{"type":"json_schema","name":"warehouse_visual_v1_1","strict":True,"schema":EXTRACTION_SCHEMA}},"input":[{"role":"user","content":content}]},timeout=180)
    response.raise_for_status()
    result=response.json()
    output="\\n".join(part.get("text","") for item in result.get("output",[]) for part in item.get("content",[]) if part.get("type")=="output_text")
    parsed=json.loads(output)
    if parsed.get("schema_version")!="warehouse_visual_v1_1":raise ValueError("Extraction schema version mismatch")
    return parsed,result.get("usage",{}),result.get("model","gpt-4.1-mini")
def process(event):
    cfg=secret()
    rid=event.get("processing_run_id")
    uuid.UUID(rid)
    found=api(cfg,"GET","bottle_processing_runs",params={"id":"eq."+rid,"select":"*"})
    if len(found)!=1:return {"status":"not_found","id":rid}
    run=found[0]
    if run["status"] not in ("queued","retry_pending"):return {"status":"not_claimable","id":rid,"current_status":run["status"]}
    claimed=api(cfg,"PATCH","bottle_processing_runs",
        {"status":"processing","claimed_at":now(),"attempt_count":(run.get("attempt_count") or 0)+1},
        params={"id":"eq."+rid,"status":"eq."+run["status"],"select":"id"})
    if len(claimed)!=1:return {"status":"claimed_elsewhere","id":rid}
    try:
        ids=run.get("source_media_ids") or []
        if not ids:raise RuntimeError("No source photographs")
        media=api(cfg,"GET","media",params={"bottle_id":"eq."+run["bottle_id"],"select":"*"})
        by_id={x["id"]:x for x in media}
        ordered=[by_id[x] for x in ids]
        photos=[];paths=[];fallback=[]
        session=new_session("u2netp")
        for m in ordered:
            path,im,result=prep(cfg,run,m,session)
            paths.append(path);photos.append(im)
            if result!="completed":fallback.append(m["id"])
        bottle=api(cfg,"GET","bottles",params={"id":"eq."+run["bottle_id"],"select":"data"})
        primary_id=(bottle[0].get("data") or {}).get("processing",{}).get("primary_media_id") if bottle else None
        primary=ids.index(primary_id) if primary_id in ids else 0
        thumb=thumbnail(cfg,run,photos[primary])
        parsed,usage,model=extract(cfg,run,paths)
        if re.fullmatch(r"4\s*/\s*5\s*(?:u\.?s\.?\s*)?(?:quart|qt)\.?s?",str(parsed.get("specification",{}).get("volume_label_text","")).strip(),flags=re.I):
            parsed["specification"]["volume_ml"]=757
        cost={"estimated_total_usd":round(((usage.get("input_tokens") or 0)*0.4+(usage.get("output_tokens") or 0)*1.6)/1000000,8)}
        result_path=f"runs/aws/{rid}/result.json"
        artifact={"schema_version":"warehouse_visual_v1_1","extraction":parsed,"model":model,"usage":usage,"cost":cost,"background_fallback_media_ids":fallback,"prompt":EXTRACTION_PROMPT}
        storage(cfg,"POST","warehouse-media",result_path,json.dumps(artifact).encode(),"application/json")
        api(cfg,"PATCH","bottle_processing_runs",{"status":"completed","schema_version":"warehouse_visual_v1_1","prompt_version":"warehouse_visual_v1_1","model":model,"working_image_paths":paths,"thumbnail_path":thumb,"extraction_json":parsed,"usage_json":usage,"cost_json":cost,"completed_at":now(),"error_message":None},params={"id":"eq."+rid})
        if bottle:
            data=bottle[0].get("data") or {};p=data.get("processing") or {}
            p.update({"status":"ready","latest_run_id":rid,"thumbnail_path":thumb,"extracted_identity":parsed.get("identity"),"extracted_specification":parsed.get("specification")})
            data["processing"]=p
            api(cfg,"PATCH","bottles",{"data":data},params={"id":"eq."+run["bottle_id"]})
        return {"status":"completed","id":rid,"photos":len(paths),"background_fallback":len(fallback)}
    except Exception as err:
        print(traceback.format_exc())
        attempt=(run.get("attempt_count") or 0)+1
        state="failed" if attempt>=3 else "retry_pending"
        api(cfg,"PATCH","bottle_processing_runs",{"status":state,"error_message":str(err)[:1000]},params={"id":"eq."+rid})
        return {"status":state,"id":rid,"error":str(err)[:500]}
def handler(event,context):
    return process(event or {})
