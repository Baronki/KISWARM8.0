"""
KISWARM v6.3.5 Test Configuration
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'python'))


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def sample_task():
    return {
        'operation': 'banking/transfer',
        'params': {'recipient': 'ki-entity-789', 'amount': 500}
    }
