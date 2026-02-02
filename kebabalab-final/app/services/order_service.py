from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from ..models import Cart, Order, OrderRequest
from ..storage import storage


class OrderService:
    def create_order(self, request: OrderRequest) -> Order:
        order = Order(
            id=str(uuid4()),
            created_at=datetime.utcnow(),
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            cart=request.cart,
            notes=request.notes,
            status="pending",
        )
        storage.save(order)
        return order

    def get_order(self, order_id: str) -> Order | None:
        return storage.get(order_id)

    def price_cart(self, cart: Cart) -> dict:
        line_items = [
            {
                "item": item.name,
                "quantity": item.quantity,
                "total": round(item.total_price, 2),
            }
            for item in cart.items
        ]
        return {
            "line_items": line_items,
            "subtotal": round(cart.total, 2),
        }


order_service = OrderService()
