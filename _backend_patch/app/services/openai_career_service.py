import json
from fastapi import HTTPException
from openai import AsyncOpenAI
from app.core.integration_settings import settings
from app.services.integration_db import connect,utc_now_iso

RULES="""Use only supplied candidate facts. Never invent employers, dates, qualifications, salaries, metrics, achievements, responsibilities, skills, company facts or hiring outcomes. Clearly flag missing evidence. Do not predict hiring probability."""

async def generate_json(user_id:str,feature:str,instructions:str,payload:dict):
    if not settings.openai_api_key: raise HTTPException(503,"OPENAI_API_KEY is not configured.")
    try:
        client=AsyncOpenAI(api_key=settings.openai_api_key)
        response=await client.responses.create(model=settings.openai_model,instructions=RULES+"\n"+instructions,input=json.dumps(payload),text={"format":{"type":"json_object"}})
        usage=getattr(response,"usage",None)
        with connect() as db:
            db.execute("INSERT INTO ai_usage_events(user_id,feature,model,openai_request_id,input_tokens,output_tokens,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (user_id,feature,settings.openai_model,getattr(response,"_request_id",None),getattr(usage,"input_tokens",None),getattr(usage,"output_tokens",None),"success",utc_now_iso()))
        return json.loads(response.output_text)
    except Exception as exc:
        raise HTTPException(502,"AI request failed.") from exc
