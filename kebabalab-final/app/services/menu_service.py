from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..config import config
from ..models import Menu


class MenuService:
    def __init__(self, menu_path: str) -> None:
        self.menu_path = Path(menu_path)

    def load(self) -> Menu:
        payload = json.loads(self.menu_path.read_text(encoding="utf-8"))
        return Menu(**payload)

    def update(self, payload: Dict) -> Menu:
        payload["updated_at"] = datetime.utcnow().isoformat()
        self.menu_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return Menu(**payload)


menu_service = MenuService(config.menu_path)
