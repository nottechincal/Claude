from __future__ import annotations

import base64
from typing import Optional

import requests

from ..config import config


class TwilioClient:
    def __init__(self) -> None:
        self.account_sid = config.twilio_account_sid
        self.auth_token = config.twilio_auth_token
        self.from_number = config.twilio_from_number

    def enabled(self) -> bool:
        return all([self.account_sid, self.auth_token, self.from_number])

    def send_sms(self, to_number: str, body: str) -> Optional[str]:
        if not self.enabled():
            return None

        auth_bytes = f"{self.account_sid}:{self.auth_token}".encode("utf-8")
        auth_header = base64.b64encode(auth_bytes).decode("utf-8")
        payload = {
            "From": self.from_number,
            "To": to_number,
            "Body": body,
        }
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
            data=payload,
            headers={"Authorization": f"Basic {auth_header}"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("sid")


twilio_client = TwilioClient()
