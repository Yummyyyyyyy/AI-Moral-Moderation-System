"""Member D's polisher service adapter.

Calls the Flask `/inference` endpoint exposed by Siwei's Colab notebook through
ngrok. The ngrok URL changes on every Colab restart, so we resolve it at call
time from a Google Drive text file (the same `file_id` Siwei's client uses).

The polisher must never crash the pipeline: any network / decoding error
returns the input draft unchanged and logs a warning.
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Drive file holding the current ngrok URL; written by Siwei on Colab boot.
_DRIVE_FILE_ID = "13LPNFgTntdH6Kw1J7iGSQLtYubuTeX5C"
_DRIVE_URL = f"https://drive.google.com/uc?id={_DRIVE_FILE_ID}&export=download"

# Module-level cache survives across factory re-instantiations.
_url_cache: str | None = None


def _fetch_url_from_drive(timeout: float) -> str | None:
    """Read the polisher's current ngrok URL from the shared Drive file."""
    try:
        resp = httpx.get(_DRIVE_URL, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        url = resp.text.strip()
        if not url.startswith("http"):
            logger.warning("polisher URL from Drive looks invalid: %r", url[:80])
            return None
        return url
    except Exception as exc:
        logger.warning("failed to fetch polisher URL from Drive: %s", exc)
        return None


def _call_polisher(base_url: str, text: str, timeout: float) -> str:
    """POST to {base_url}/inference and return the polished string."""
    resp = httpx.post(
        f"{base_url}/inference",
        json={"text": text},
        timeout=timeout,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "response" not in payload:
        raise RuntimeError(f"polisher response missing 'response' key: {payload}")
    return payload["response"]


class TeamPolisher:
    """Live polisher backed by Siwei's Colab+ngrok service."""

    version = "team-polisher-v1"

    def __init__(self) -> None:
        """Read timeout and (optional) explicit URL from settings."""
        self._timeout = settings.polisher_timeout
        # If the user pinned a URL via MMS_POLISHER_URL, prefer it over Drive.
        self._explicit_url = settings.polisher_url or None

    def polish(self, text: str) -> str:
        """Try once, refresh URL, try again. On total failure return ``text``."""
        global _url_cache
        for attempt in range(2):
            url = self._explicit_url or _url_cache
            if url is None:
                url = _fetch_url_from_drive(self._timeout)
                if url is None:
                    return text
                _url_cache = url
            try:
                return _call_polisher(url, text, self._timeout)
            except Exception as exc:
                logger.warning("polish attempt %d failed: %s", attempt + 1, exc)
                if not self._explicit_url:
                    _url_cache = None  # force refresh on retry
        logger.warning("polisher gave up; returning unpolished draft")
        return text