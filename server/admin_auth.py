"""Authentication helpers for the CommentScope researcher dashboard."""
import hmac
import os
from typing import Optional, Tuple


SESSION_COOKIE_NAME = "comment_scope_admin_session"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"
DEFAULT_SESSION_SECRET = "comment-scope-local-admin-session-secret"


class AdminAuth:
    """Read administrator credentials and manage a signed Tornado cookie."""

    def credentials(self) -> Tuple[str, str]:
        return (
            os.environ.get("ADMIN_USERNAME", DEFAULT_USERNAME),
            os.environ.get("ADMIN_PASSWORD", DEFAULT_PASSWORD),
        )

    def session_secret(self) -> str:
        return os.environ.get("ADMIN_SESSION_SECRET", DEFAULT_SESSION_SECRET)

    def verify_credentials(self, username: str, password: str) -> bool:
        configured_username, configured_password = self.credentials()
        return hmac.compare_digest(str(username), configured_username) and hmac.compare_digest(
            str(password), configured_password
        )

    def set_session(self, handler, username: str) -> None:
        handler.set_secure_cookie(
            SESSION_COOKIE_NAME,
            username,
            expires_days=1,
            httponly=True,
            samesite="lax",
            secure=os.environ.get("ADMIN_COOKIE_SECURE", "0") == "1",
        )

    def clear_session(self, handler) -> None:
        handler.clear_cookie(SESSION_COOKIE_NAME, httponly=True, samesite="lax")

    def session_username(self, handler) -> Optional[str]:
        value = handler.get_secure_cookie(SESSION_COOKIE_NAME, max_age_days=1)
        if value is None:
            return None
        try:
            username = value.decode("utf-8")
        except UnicodeDecodeError:
            return None
        configured_username, _ = self.credentials()
        if not hmac.compare_digest(username, configured_username):
            return None
        return username

    def is_authenticated(self, handler) -> bool:
        return self.session_username(handler) is not None
