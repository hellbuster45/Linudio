from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

_url = make_url(settings.DATABASE_URL)
_is_sqlite = _url.get_backend_name() == "sqlite"

_engine_kwargs = {}
if _is_sqlite:
    if _url.database and _url.database != ":memory:":
        Path(_url.database).parent.mkdir(parents=True, exist_ok=True)
    # FastAPI runs sync routes and background tasks on worker threads, so the
    # connection must be usable from threads other than the one that made it.
    _engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}

engine = create_engine(url=settings.DATABASE_URL, **_engine_kwargs)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        # WAL lets the status-polling reads proceed while a background task writes.
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Creates any missing tables. Safe to call on every startup (existing
    tables are left untouched)."""
    # Importing the model modules registers their tables on Base.metadata.
    from api.v1.stt import models as _stt_models  # noqa: F401
    from api.v1.videos import models as _videos_models  # noqa: F401
    from api.v1.tts import models as _tts_models  # noqa: F401
    Base.metadata.create_all(bind=engine)

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
