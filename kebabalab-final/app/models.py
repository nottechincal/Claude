from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BusinessHours(BaseModel):
    day: str
    open: str
    close: str


class BusinessProfile(BaseModel):
    name: str
    phone: str
    address: str
    timezone: str
    hours: List[BusinessHours]
    rules: List[str] = Field(default_factory=list)


class MenuOption(BaseModel):
    name: str
    price_delta: float = 0.0


class MenuItem(BaseModel):
    id: str
    name: str
    category: str
    base_price: float
    options: List[MenuOption] = Field(default_factory=list)


class Menu(BaseModel):
    updated_at: datetime
    items: List[MenuItem]


class CartItemOption(BaseModel):
    name: str
    value: str
    price_delta: float = 0.0


class CartItem(BaseModel):
    item_id: str
    name: str
    quantity: int = 1
    base_price: float
    options: List[CartItemOption] = Field(default_factory=list)

    @property
    def total_price(self) -> float:
        option_total = sum(option.price_delta for option in self.options)
        return (self.base_price + option_total) * self.quantity


class Cart(BaseModel):
    items: List[CartItem] = Field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(item.total_price for item in self.items)


class OrderRequest(BaseModel):
    customer_name: str
    customer_phone: str
    cart: Cart
    notes: Optional[str] = None


class Order(BaseModel):
    id: str
    created_at: datetime
    customer_name: str
    customer_phone: str
    cart: Cart
    notes: Optional[str] = None
    status: str = "pending"


class VapiToolRequest(BaseModel):
    tool: str
    arguments: dict = Field(default_factory=dict)
    callId: Optional[str] = None
    conversationId: Optional[str] = None


class VapiToolResponse(BaseModel):
    result: dict
    callId: Optional[str] = None
