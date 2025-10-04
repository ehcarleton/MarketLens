import pytest
from pathlib import Path
import tempfile


@pytest.fixture(scope="session")
def temp_dir() -> Path:
    """Create a temporary directory for test artifacts (like DuckDB files)."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)
