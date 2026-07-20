from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from app.services.integration_db import connect, utc_now_iso

def get_plan(code: str):
    with connect() as db:
        row=db.execute("SELECT * FROM subscription_plans WHERE code=? AND is_active=1",(code,)).fetchone()
    if not row: raise HTTPException(404,"Plan not found.")
    return dict(row)

def get_current_subscription(user_id: str):
    with connect() as db:
        row=db.execute("SELECT * FROM candidate_subscriptions WHERE user_id=? ORDER BY id DESC LIMIT 1",(user_id,)).fetchone()
    return dict(row) if row else None

def require_active_access(user_id: str):
    s=get_current_subscription(user_id)
    if not s or s["status"] not in ("active","non_renewing") or not s.get("current_period_end"):
        raise HTTPException(402,{"error":"subscription_required","upgrade_url":"/pricing"})
    if datetime.fromisoformat(s["current_period_end"]) <= datetime.now(timezone.utc):
        raise HTTPException(402,{"error":"subscription_expired","upgrade_url":"/pricing"})

def activate_access(user_id: str, plan_code: str, customer_code=None, subscription_code=None, email_token=None):
    plan=get_plan(plan_code); start=datetime.now(timezone.utc); end=start+timedelta(days=int(plan["access_days"])); now=utc_now_iso()
    with connect() as db:
        db.execute("UPDATE candidate_subscriptions SET status='expired',updated_at=? WHERE user_id=? AND status IN ('active','non_renewing','attention')",(now,user_id))
        cur=db.execute("""INSERT INTO candidate_subscriptions(user_id,plan_code,status,paystack_customer_code,paystack_subscription_code,paystack_email_token,current_period_start,current_period_end,created_at,updated_at)
        VALUES(?,?,'active',?,?,?,?,?,?,?)""",(user_id,plan_code,customer_code,subscription_code,email_token,start.isoformat(),end.isoformat(),now,now))
        row=db.execute("SELECT * FROM candidate_subscriptions WHERE id=?",(cur.lastrowid,)).fetchone()
    return dict(row)

def mark_non_renewing(user_id: str):
    now=utc_now_iso()
    with connect() as db:
        db.execute("""UPDATE candidate_subscriptions SET status='non_renewing',cancel_at_period_end=1,cancelled_at=?,updated_at=?
        WHERE id=(SELECT id FROM candidate_subscriptions WHERE user_id=? ORDER BY id DESC LIMIT 1)""",(now,now,user_id))
        row=db.execute("SELECT * FROM candidate_subscriptions WHERE user_id=? ORDER BY id DESC LIMIT 1",(user_id,)).fetchone()
    if not row: raise HTTPException(404,"No subscription found.")
    return dict(row)
