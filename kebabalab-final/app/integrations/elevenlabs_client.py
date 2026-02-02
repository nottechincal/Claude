from __future__ import annotations

from typing import Optional

import requests

from ..config import config


class ElevenLabsClient:
    def __init__(self) -> None:
        self.api_key = config.elevenlabs_api_key
        self.voice_id = config.elevenlabs_voice_id

    def enabled(self) -> bool:
        return bool(self.api_key and self.voice_id)

    def text_to_speech(self, text: str) -> Optional[bytes]:
        if not self.enabled():
            return None

        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.8,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.content


elevenlabs_client = ElevenLabsClient()
