import os
from typing import List, Dict, Optional
import json


def getenv_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def parse_csv_env(name: str) -> List[str]:
    raw = os.getenv(name)
    if not raw:
        return []
    return [part.strip() for part in raw.split(',') if part.strip()]


class Settings:
    def __init__(self) -> None:
        # CORS / Origins
        origins = parse_csv_env("FRONTEND_ORIGINS")
        if not origins:
            single = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
            origins = [single]
        self.FRONTEND_ORIGINS: List[str] = origins

        # HTTPS and cookies
        self.FORCE_HTTPS: bool = getenv_bool("FORCE_HTTPS", False)
        self.HSTS_ENABLE: bool = getenv_bool("HSTS_ENABLE", False)
        self.COOKIE_SECURE: bool = getenv_bool("COOKIE_SECURE", False)
        self.COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")

        # CSP extras
        extra = parse_csv_env("CSP_CONNECT_EXTRA")
        if not extra:
            extra = ["https://www.googleapis.com"]
        self.CSP_CONNECT_EXTRA: List[str] = extra

        # CSRF
        self.CSRF_ENABLE: bool = getenv_bool("CSRF_ENABLE", False)
        self.CSRF_HEADER_NAME: str = os.getenv("CSRF_HEADER_NAME", "x-csrf-token")
        self.CSRF_COOKIE_NAME: str = os.getenv("CSRF_COOKIE_NAME", "csrf_token")

        # Integrations behavior
        self.INTEGRATION_CLOSE_MODE: str = os.getenv("INTEGRRATION_CLOSE_MODE", "archive").lower() if os.getenv("INTEGRRATION_CLOSE_MODE") else os.getenv("INTEGRATION_CLOSE_MODE", "archive").lower()

        # Email / SMTP
        self.EMAIL_TRANSPORT: str = os.getenv("LIFERPG_EMAIL_TRANSPORT", "console").lower()  # console|smtp|disabled
        self.SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
        self.SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
        self.SMTP_USE_TLS: bool = getenv_bool("SMTP_USE_TLS", True)
        self.SMTP_FROM: Optional[str] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", None))

        # Provider concurrency caps (optional per-provider overrides)
        # Example env: SYNC_PROVIDER_CAPS='{"todoist":2,"github":3}'
        caps_raw = os.getenv("SYNC_PROVIDER_CAPS")
        caps: Dict[str, int] = {}
        if caps_raw:
            try:
                data = json.loads(caps_raw)
                if isinstance(data, dict):
                    for k, v in data.items():
                        try:
                            iv = int(v)
                            if iv > 0:
                                caps[str(k)] = iv
                        except Exception:
                            continue
            except Exception:
                caps = {}
        self.PROVIDER_CAPS: Dict[str, int] = caps
        self.DEFAULT_PROVIDER_CAP: int = int(os.getenv('SYNC_MAX_CONCURRENCY_PER_PROVIDER', '4'))

    def csp_header(self) -> str:
        connect_src = " ".join(["'self'", *self.CSP_CONNECT_EXTRA])
        # Allow inline styles in dev to keep things simple; consider removing in prod
        return "; ".join([
            "default-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "object-src 'none'",
            "img-src 'self' data:",
            f"connect-src {connect_src}",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",
        ])


settings = Settings()
