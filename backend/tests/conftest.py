import os
import sys
import tempfile
from pathlib import Path

# Must run before anything imports core.config: point storage and the database at a throwaway
# directory so tests never touch real data or a developer's Postgres.
_tmp = Path(tempfile.mkdtemp(prefix="linudio-test-"))
os.environ["STORAGE_DIR"] = str(_tmp)
os.environ["DATABASE_URL"] = f"sqlite:///{(_tmp / 'test.db').as_posix()}"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def client():
    from main import app
    with TestClient(app) as test_client:  # `with` runs the startup hook (creates the tables)
        yield test_client
