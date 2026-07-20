import hashlib,hmac,httpx
from fastapi import HTTPException
from app.core.integration_settings import settings

class PaystackService:
    base="https://api.paystack.co"
    def headers(self):
        if not settings.paystack_secret_key: raise HTTPException(503,"PAYSTACK_SECRET_KEY is not configured.")
        return {"Authorization":f"Bearer {settings.paystack_secret_key}","Content-Type":"application/json"}
    async def post(self,path,payload):
        async with httpx.AsyncClient(timeout=30) as c: r=await c.post(self.base+path,headers=self.headers(),json=payload)
        d=r.json()
        if r.is_error or not d.get("status"): raise HTTPException(502,d.get("message","Paystack request failed."))
        return d["data"]
    async def get(self,path):
        async with httpx.AsyncClient(timeout=30) as c: r=await c.get(self.base+path,headers=self.headers())
        d=r.json()
        if r.is_error or not d.get("status"): raise HTTPException(502,d.get("message","Paystack request failed."))
        return d["data"]
    def valid_signature(self,raw:bytes,sig:str|None):
        if not sig or not settings.paystack_secret_key:return False
        expected=hmac.new(settings.paystack_secret_key.encode(),raw,hashlib.sha512).hexdigest()
        return hmac.compare_digest(expected,sig)
paystack=PaystackService()
