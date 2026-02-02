from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from .config import config
from .models import Cart, Order


class OrderStorage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_phone TEXT NOT NULL,
                    cart_json TEXT NOT NULL,
                    notes TEXT,
                    status TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def save(self, order: Order) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO orders
                (id, created_at, customer_name, customer_phone, cart_json, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order.id,
                    order.created_at.isoformat(),
                    order.customer_name,
                    order.customer_phone,
                    order.cart.model_dump_json(),
                    order.notes,
                    order.status,
                ),
            )

    def get(self, order_id: str) -> Optional[Order]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT id, created_at, customer_name, customer_phone, cart_json, notes, status "
                "FROM orders WHERE id = ?",
                (order_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            cart_json = Cart(**json.loads(row[4]))
            return Order(
                id=row[0],
                created_at=datetime.fromisoformat(row[1]),
                customer_name=row[2],
                customer_phone=row[3],
                cart=cart_json,
                notes=row[5],
                status=row[6],
            )

    def list_all(self) -> Iterable[Order]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT id, created_at, customer_name, customer_phone, cart_json, notes, status FROM orders"
            )
            for row in cursor.fetchall():
                cart_json = Cart(**json.loads(row[4]))
                yield Order(
                    id=row[0],
                    created_at=datetime.fromisoformat(row[1]),
                    customer_name=row[2],
                    customer_phone=row[3],
                    cart=cart_json,
                    notes=row[5],
                    status=row[6],
                )


storage = OrderStorage(config.sqlite_path)
