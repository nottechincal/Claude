"""
Order management REST API.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import order as order_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


class OrderStatusUpdate(BaseModel):
    status: str


@router.get("")
async def list_orders(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Get recent orders for the dashboard."""
    orders = await order_service.get_recent_orders(db, limit=limit)
    return {"orders": orders, "count": len(orders)}


@router.get("/{order_id}")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific order."""
    order = await order_service.get_order(order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status")
async def update_status(
    order_id: str,
    body: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update order status (confirmed → preparing → ready → completed)."""
    valid_statuses = {"confirmed", "preparing", "ready", "completed", "cancelled"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    result = await order_service.update_order_status(order_id, body.status, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
