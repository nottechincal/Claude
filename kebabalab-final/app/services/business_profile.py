from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from ..config import config
from ..models import BusinessProfile


class BusinessProfileService:
    def __init__(self, profile_path: str) -> None:
        self.profile_path = Path(profile_path)

    def load(self) -> BusinessProfile:
        payload = json.loads(self.profile_path.read_text(encoding="utf-8"))
        return BusinessProfile(**payload)

    def update(self, payload: Dict) -> BusinessProfile:
        self.profile_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return BusinessProfile(**payload)


business_profile_service = BusinessProfileService(config.business_profile_path)
