import os, json, io, uuid, re, traceback
from datetime import datetime, timezone
import requests
from PIL import Image, ImageOps
from rembg import remove, new_session

TIMEOUT=40
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
    if mime: headers.update({"Content-Type":mime,"x-upsert":"false"})
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
    content=[{"type":"input_text","text":"Extract visible bottle facts from all photographs together; do not speculate. Return JSON with keys identity, production, specification, identifiers, special_features, condition, label_transcriptions, evidence, uncertainties. In particular, distinguish tax stamp numbers from Warehouse inventory stickers; 4/5 US quart = 757mL. Preserve uncertainty and label text. Do not use generated thumbnail for extraction."}]
    for i,path in enumerate(paths):
        b=storage(cfg,"GET","warehouse-media",path)
        import base64
        content.append({"type":"input_text","text":f"Image {i+1}"})
        content.append({"type":"input_image","image_url":"data:image/jpeg;base64,"+base64.b64encode(b).decode(),"detail":"high"})
    response=requests.post("https://api.openai.com/v1/responses",
        headers={"Authorization":"Bearer "+cfg["OPENAI_API_KEY"],"Content-Type":"application/json"},
        json={"model":"gpt-4.1-mini","store":False,"max_output_tokens":3500,"input":[{"role":"user","content":content}]},timeout=180)
    response.raise_for_status();result=response.json()
    text="\n".join(part.get("text","") for item in result.get("output",[]) for part in item.get("content",[]) if part.get("type")=="output_text").strip()
    if text.startswith("```"):text=re.sub(r"^```(?:json)?\s*|\s*```$","",text).strip()
    data=json.loads(text)
    return data,result.get("usage",{}),result.get("model","gpt-4.1-mini")
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
        if str(parsed.get("specification",{}).get("volume_label_text","")).strip().lower() in ("4/5 quart","4/5 qt"):
            parsed["specification"]["volume_ml"]=757
        cost={"estimated_total_usd":round(((usage.get("input_tokens") or 0)*0.4+(usage.get("output_tokens") or 0)*1.6)/1000000,8)}
        result_path=f"runs/aws/{rid}/result.json"
        artifact={"schema_version":"warehouse_visual_aws_v1","extraction":parsed,"model":model,"usage":usage,"cost":cost,"background_fallback_media_ids":fallback}
        storage(cfg,"POST","warehouse-media",result_path,json.dumps(artifact).encode(),"application/json")
        api(cfg,"PATCH","bottle_processing_runs",{"status":"completed","schema_version":"warehouse_visual_aws_v1","prompt_version":"aws_worker_v1","model":model,"working_image_paths":paths,"thumbnail_path":thumb,"extraction_json":parsed,"usage_json":usage,"cost_json":cost,"completed_at":now(),"error_message":None},params={"id":"eq."+rid})
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
