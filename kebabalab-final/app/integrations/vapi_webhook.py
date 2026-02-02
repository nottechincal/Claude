from __future__ import annotations

import hashlib
import hmac
from typing import Optional

from fastapi import Header, HTTPException

from ..config import config


def verify_signature(payload: bytes, signature: Optional[str]) -> None:
    if not config.vapi_webhook_secret:
        return
    if not signature:
        raise HTTPException(status_code=401, detail="Missing Vapi signature")
    digest = hmac.new(
        config.vapi_webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(digest, signature):
        raise HTTPException(status_code=401, detail="Invalid Vapi signature")


def extract_signature(x_vapi_signature: Optional[str]) -> Optional[str]:
    return x_vapi_signature
