"""
Web Chat Channel via WebSocket
Real-time streaming chat for the web interface.
Claude's responses stream in token by token.
"""

import json
import logging
import uuid
from functools import partial

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ai.agent import OrderingAgent
from app.database import AsyncSessionLocal
from app.services.tool_executor import execute_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["webchat"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    Streams Claude's responses token by token.
    """
    await websocket.accept()
    session_id = f"web_{uuid.uuid4().hex[:12]}"
    phone_number = "web_user"  # Web users don't have a phone number

    logger.info(f"WebSocket connected: {session_id}")

    # Send welcome
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "message": "Connected to Cranny Boys Pizza AI. What can I get for you today? 🍕",
    })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                phone_number = message_data.get("phone", phone_number)
            except json.JSONDecodeError:
                user_message = data

            if not user_message.strip():
                continue

            # Signal that we're thinking
            await websocket.send_json({"type": "thinking"})

            agent = OrderingAgent(
                session_id=session_id,
                phone_number=phone_number,
                channel="web",
            )

            # Stream the response
            async with AsyncSessionLocal() as db:
                tool_fn = partial(execute_tool, db=db, channel="web")
                full_response = ""

                try:
                    async for chunk in agent.chat_stream(user_message, tool_fn):
                        full_response += chunk
                        await websocket.send_json({
                            "type": "chunk",
                            "text": chunk,
                        })
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    # Fallback to non-streaming
                    full_response = await agent.chat(user_message, tool_fn)
                    await websocket.send_json({
                        "type": "chunk",
                        "text": full_response,
                    })

            # Signal response complete
            await websocket.send_json({
                "type": "done",
                "full_response": full_response,
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error [{session_id}]: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "Something went wrong"})
            await websocket.close()
        except Exception:
            pass
