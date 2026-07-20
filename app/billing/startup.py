from app.billing.db import Base, engine, SessionLocal
from app.billing.service import seed_plans


def initialise_billing() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_plans(db)
