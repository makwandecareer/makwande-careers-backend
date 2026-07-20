import json,secrets,hashlib
from fastapi import APIRouter,Depends,Header,HTTPException,Request
from pydantic import BaseModel,EmailStr
from app.core.integration_settings import settings
from app.services.integration_auth import current_user_id
from app.services.integration_db import connect,json_dumps,utc_now_iso
from app.services.paystack_service import paystack
from app.services.subscription_service import get_plan,get_current_subscription,activate_access,mark_non_renewing

router=APIRouter(prefix="/billing",tags=["Billing"])

class CheckoutRequest(BaseModel):
    plan_code:str
    email:EmailStr
class VerifyRequest(BaseModel):
    reference:str

@router.get("/plans")
async def plans():
    with connect() as db: rows=db.execute("SELECT code,name,amount_subunits,currency,access_days,is_recurring FROM subscription_plans WHERE is_active=1 ORDER BY amount_subunits").fetchall()
    return {"plans":[dict(r) for r in rows]}

@router.get("/subscription")
async def subscription(user_id:str=Depends(current_user_id)):
    return {"subscription":get_current_subscription(user_id)}

@router.post("/checkout")
async def checkout(body:CheckoutRequest,user_id:str=Depends(current_user_id)):
    plan=get_plan(body.plan_code); ref=f"MC-{user_id}-{secrets.token_hex(8)}"
    payload={"email":str(body.email),"amount":str(plan["amount_subunits"]),"currency":plan["currency"],"reference":ref,"callback_url":f"{settings.frontend_url}/billing/callback","metadata":json.dumps({"user_id":user_id,"plan_code":plan["code"]})}
    if plan["is_recurring"]:
        if not settings.paystack_premium_plan_code: raise HTTPException(503,"PAYSTACK_PREMIUM_PLAN_CODE is not configured.")
        payload["plan"]=settings.paystack_premium_plan_code
    now=utc_now_iso()
    with connect() as db: db.execute("INSERT INTO payment_transactions(user_id,plan_code,reference,amount_subunits,currency,status,created_at,updated_at) VALUES(?,?,?,?,?,'pending',?,?)",(user_id,plan["code"],ref,plan["amount_subunits"],plan["currency"],now,now))
    return await paystack.post("/transaction/initialize",payload)

@router.post("/verify")
async def verify(body:VerifyRequest,user_id:str=Depends(current_user_id)):
    with connect() as db: row=db.execute("SELECT * FROM payment_transactions WHERE reference=? AND user_id=?",(body.reference,user_id)).fetchone()
    if not row: raise HTTPException(404,"Payment reference not found.")
    data=await paystack.get(f"/transaction/verify/{body.reference}")
    if data.get("status")!="success" or int(data.get("amount",-1))!=int(row["amount_subunits"]) or data.get("currency")!=row["currency"]:
        raise HTTPException(400,"Payment verification failed.")
    customer=data.get("customer") or {}; sub=data.get("subscription") or {}
    active=activate_access(user_id,row["plan_code"],customer.get("customer_code"),sub.get("subscription_code") if isinstance(sub,dict) else None,sub.get("email_token") if isinstance(sub,dict) else None)
    with connect() as db: db.execute("UPDATE payment_transactions SET status='success',paystack_transaction_id=?,channel=?,paid_at=?,verified_at=?,gateway_payload=?,updated_at=? WHERE reference=?",(str(data.get("id","")),data.get("channel"),data.get("paid_at"),utc_now_iso(),json_dumps(data),utc_now_iso(),body.reference))
    return {"subscription":active}

@router.post("/cancel")
async def cancel(user_id:str=Depends(current_user_id)):
    s=get_current_subscription(user_id)
    if not s: raise HTTPException(404,"No subscription found.")
    if s.get("paystack_subscription_code") and s.get("paystack_email_token"):
        await paystack.post("/subscription/disable",{"code":s["paystack_subscription_code"],"token":s["paystack_email_token"]})
    return {"subscription":mark_non_renewing(user_id)}

@router.post("/webhook")
async def webhook(request:Request,x_paystack_signature:str|None=Header(default=None)):
    raw=await request.body()
    if not paystack.valid_signature(raw,x_paystack_signature): raise HTTPException(401,"Invalid webhook signature.")
    payload=json.loads(raw); event=payload.get("event","unknown"); data=payload.get("data") or {}
    key=f"{event}:{data.get('id') or data.get('reference') or data.get('subscription_code') or hashlib.sha256(raw).hexdigest()}"
    with connect() as db:
        if db.execute("SELECT 1 FROM billing_events WHERE event_key=?",(key,)).fetchone(): return {"received":True}
        db.execute("INSERT INTO billing_events(event_key,event_type,payload,created_at) VALUES(?,?,?,?)",(key,event,json_dumps(payload),utc_now_iso()))
        if event=="subscription.not_renew":
            db.execute("UPDATE candidate_subscriptions SET status='non_renewing',cancel_at_period_end=1,updated_at=? WHERE paystack_subscription_code=?",(utc_now_iso(),data.get("subscription_code")))
        elif event=="subscription.disable":
            db.execute("UPDATE candidate_subscriptions SET status='expired',updated_at=? WHERE paystack_subscription_code=?",(utc_now_iso(),data.get("subscription_code")))
        elif event=="invoice.payment_failed":
            code=(data.get("subscription") or {}).get("subscription_code")
            db.execute("UPDATE candidate_subscriptions SET status='attention',updated_at=? WHERE paystack_subscription_code=?",(utc_now_iso(),code))
        db.execute("UPDATE billing_events SET processed=1,processed_at=? WHERE event_key=?",(utc_now_iso(),key))
    return {"received":True}
