import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from admin_auth import AdminAuth  # noqa: E402


def test_default_credentials_are_admin_admin123(monkeypatch):
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    auth = AdminAuth()
    assert auth.credentials() == ("admin", "admin123")


def test_environment_credentials_override_defaults(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "researcher")
    monkeypatch.setenv("ADMIN_PASSWORD", "strong-test-password")
    assert AdminAuth().credentials() == ("researcher", "strong-test-password")


def test_password_comparison_is_false_for_wrong_password(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin123")
    auth = AdminAuth()
    assert auth.verify_credentials("admin", "wrong") is False
    assert auth.verify_credentials("other", "admin123") is False
    assert auth.verify_credentials("admin", "admin123") is True
