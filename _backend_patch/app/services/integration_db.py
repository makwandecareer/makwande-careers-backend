from __future__ import annotations
import json, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator
from app.core.integration_settings import settings

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(settings.database_path)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    finally:
        db.close()

def initialise_integration_schema() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS subscription_plans(
          id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
          amount_subunits INTEGER NOT NULL, currency TEXT NOT NULL DEFAULT 'ZAR',
          access_days INTEGER NOT NULL, is_recurring INTEGER NOT NULL DEFAULT 0,
          paystack_plan_code TEXT, is_active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS candidate_subscriptions(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, plan_code TEXT NOT NULL,
          status TEXT NOT NULL, paystack_customer_code TEXT, paystack_subscription_code TEXT,
          paystack_email_token TEXT, current_period_start TEXT, current_period_end TEXT,
          cancel_at_period_end INTEGER NOT NULL DEFAULT 0, cancelled_at TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payment_transactions(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, plan_code TEXT NOT NULL,
          reference TEXT UNIQUE NOT NULL, paystack_transaction_id TEXT, amount_subunits INTEGER NOT NULL,
          currency TEXT NOT NULL DEFAULT 'ZAR', status TEXT NOT NULL, channel TEXT,
          paid_at TEXT, verified_at TEXT, gateway_payload TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS billing_events(
          id INTEGER PRIMARY KEY AUTOINCREMENT, event_key TEXT UNIQUE NOT NULL, event_type TEXT NOT NULL,
          payload TEXT NOT NULL, processed INTEGER NOT NULL DEFAULT 0, processed_at TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ai_usage_events(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, feature TEXT NOT NULL,
          model TEXT NOT NULL, openai_request_id TEXT, input_tokens INTEGER, output_tokens INTEGER,
          status TEXT NOT NULL, error_message TEXT, created_at TEXT NOT NULL
        );
        """)
        now = utc_now_iso()
        db.execute("INSERT OR IGNORE INTO subscription_plans(code,name,amount_subunits,currency,access_days,is_recurring,created_at) VALUES('trial_14_day','14-Day Access',4500,'ZAR',14,0,?)",(now,))
        db.execute("INSERT OR IGNORE INTO subscription_plans(code,name,amount_subunits,currency,access_days,is_recurring,paystack_plan_code,created_at) VALUES('premium_30_day','30-Day Premium',30000,'ZAR',30,1,?,?)",(settings.paystack_premium_plan_code or None,now))

def json_dumps(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",",":"))
