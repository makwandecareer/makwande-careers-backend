from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ENGINE_OPTIONS = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_pre_ping": True,
    "pool_recycle": 1800,
    "pool_timeout": 30,
}

def create_session(database_url: str):
    engine = create_engine(database_url, **ENGINE_OPTIONS)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
