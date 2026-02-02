from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Header, HTTPException, Request
import base64
from fastapi.responses import JSONResponse

from .config import config
from .integrations.elevenlabs_client import elevenlabs_client
from .integrations.twilio_client import twilio_client
from .integrations.vapi_webhook import extract_signature, verify_signature
from .models import (
    Cart,
    Menu,
    OrderRequest,
    VapiToolRequest,
    VapiToolResponse,
)
from .services.business_profile import business_profile_service
from .services.menu_service import menu_service
from .services.order_service import order_service

app = FastAPI(title="Kebabalab Final API")


@app.get("/health")
async def health() -> dict:
    profile = business_profile_service.load()
    return {
        "status": "ok",
        "business": profile.name,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/menu", response_model=Menu)
async def get_menu() -> Menu:
    return menu_service.load()


@app.post("/menu", response_model=Menu)
async def update_menu(payload: Dict[str, Any]) -> Menu:
    return menu_service.update(payload)


@app.post("/orders")
async def create_order(request: OrderRequest) -> dict:
    order = order_service.create_order(request)
    return {
        "order_id": order.id,
        "status": order.status,
        "total": order.cart.total,
    }


@app.get("/orders/{order_id}")
async def get_order(order_id: str) -> dict:
    order = order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.model_dump()


@app.post("/voice/elevenlabs/tts")
async def elevenlabs_tts(payload: Dict[str, Any]) -> JSONResponse:
    text = payload.get("text", "")
    audio = elevenlabs_client.text_to_speech(text)
    if not audio:
        raise HTTPException(status_code=400, detail="ElevenLabs is not configured")
    encoded = base64.b64encode(audio).decode("utf-8")
    return JSONResponse(content={"audio_base64": encoded})


@app.post("/webhook/vapi")
async def vapi_webhook(
    request: Request,
    x_vapi_signature: str | None = Header(default=None),
) -> VapiToolResponse:
    raw_body = await request.body()
    verify_signature(raw_body, extract_signature(x_vapi_signature))
    payload = await request.json()
    tool_request = VapiToolRequest(**payload)
    result = await handle_tool(tool_request.tool, tool_request.arguments)
    return VapiToolResponse(result=result, callId=tool_request.callId)


async def handle_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "check_open":
        profile = business_profile_service.load()
        return {"hours": [hour.model_dump() for hour in profile.hours]}

    if tool_name == "get_business_profile":
        profile = business_profile_service.load()
        return profile.model_dump()

    if tool_name == "get_menu":
        menu = menu_service.load()
        return menu.model_dump()

    if tool_name == "price_cart":
        cart = Cart(**arguments.get("cart", {}))
        return order_service.price_cart(cart)

    if tool_name == "create_order":
        request = OrderRequest(**arguments)
        order = order_service.create_order(request)
        return {
            "order_id": order.id,
            "status": order.status,
            "total": order.cart.total,
        }

    if tool_name == "send_receipt_sms":
        to_number = arguments.get("to")
        message = arguments.get("message")
        if not to_number or not message:
            raise HTTPException(status_code=400, detail="Missing SMS arguments")
        sid = twilio_client.send_sms(to_number, message)
        return {"message_sid": sid, "sent": sid is not None}

    raise HTTPException(status_code=404, detail=f"Unknown tool '{tool_name}'")


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
