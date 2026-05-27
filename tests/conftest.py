import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))


@pytest.fixture(autouse=True)
def _restore_vault_path_env():
    """Restore VAULT_PATH env var after each test to prevent cross-test pollution."""
    original = os.environ.get("VAULT_PATH")
    yield
    if original is None:
        os.environ.pop("VAULT_PATH", None)
    else:
        os.environ["VAULT_PATH"] = original
