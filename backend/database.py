from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

engine = create_engine(url=settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    print("Entering get_db function")
    db = SessionLocal()
    try:
        print("Yielding database session")
        yield db
    except Exception as e:
        raise e
    finally:
        print("Exiting get_db function")
        db.close()