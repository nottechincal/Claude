"""
Claude AI Ordering Agent

The brain of the system. Uses Claude claude-opus-4-6 with tool use to power
natural language ordering across all channels.
"""

import json
import logging
from typing import AsyncIterator, Optional

import anthropic

from app.ai.prompts import ORDERING_SYSTEM_PROMPT, WHATSAPP_SYSTEM_PROMPT
from app.ai.tools import ORDERING_TOOLS
from app.config import get_settings
from app.redis_client import redis_get, redis_set

logger = logging.getLogger(__name__)
settings = get_settings()

# Claude clients
_client: Optional[anthropic.AsyncAnthropic] = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


SESSION_KEY = "session:{session_id}:messages"
CART_KEY = "cart:{session_id}"


async def get_session_messages(session_id: str) -> list:
    data = await redis_get(SESSION_KEY.format(session_id=session_id))
    return data if data else []


async def save_session_messages(session_id: str, messages: list) -> None:
    await redis_set(SESSION_KEY.format(session_id=session_id), messages, ttl=settings.session_ttl)


class OrderingAgent:
    """
    Multi-turn Claude AI agent for food ordering.
    Handles tool use automatically and maintains conversation history.
    """

    def __init__(self, session_id: str, phone_number: str, channel: str = "voice"):
        self.session_id = session_id
        self.phone_number = phone_number
        self.channel = channel
        self.client = get_client()

    async def chat(self, user_message: str, tool_executor) -> str:
        """
        Send a message and get Claude's response.
        Automatically handles tool use loop.
        Returns the final text response.
        """
        messages = await get_session_messages(self.session_id)
        messages.append({"role": "user", "content": user_message})

        system = WHATSAPP_SYSTEM_PROMPT if self.channel == "whatsapp" else ORDERING_SYSTEM_PROMPT
        response_text = await self._run_agent_loop(messages, system, tool_executor)

        await save_session_messages(self.session_id, messages)
        return response_text

    async def chat_stream(self, user_message: str, tool_executor) -> AsyncIterator[str]:
        """
        Streaming version — yields text chunks as they arrive.
        Used for low-latency voice responses.
        """
        messages = await get_session_messages(self.session_id)
        messages.append({"role": "user", "content": user_message})

        system = ORDERING_SYSTEM_PROMPT

        async for chunk in self._run_agent_loop_stream(messages, system, tool_executor):
            yield chunk

        await save_session_messages(self.session_id, messages)

    async def _run_agent_loop(self, messages: list, system: str, tool_executor) -> str:
        """
        Run the Claude tool-use loop until we get a final text response.
        """
        while True:
            response = await self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
                system=system,
                tools=ORDERING_TOOLS,
                messages=messages,
            )

            # Append assistant response to history
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                # Extract text response
                text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text += block.text
                return text.strip()

            if response.stop_reason == "tool_use":
                # Execute all tool calls and collect results
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        logger.info(f"Tool call: {block.name} | Input: {json.dumps(block.input)}")
                        result = await tool_executor(
                            tool_name=block.name,
                            tool_input=block.input,
                            session_id=self.session_id,
                            phone_number=self.phone_number,
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result) if not isinstance(result, str) else result,
                        })

                messages.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason
            logger.warning(f"Unexpected stop_reason: {response.stop_reason}")
            break

        return "Sorry, something went wrong. Please try again."

    async def _run_agent_loop_stream(
        self, messages: list, system: str, tool_executor
    ) -> AsyncIterator[str]:
        """
        Streaming tool-use loop. Yields text chunks while handling tools.
        """
        while True:
            full_response_content = []
            current_tool_calls = {}
            current_text = ""

            async with self.client.messages.stream(
                model="claude-haiku-4-5",  # haiku for voice speed
                max_tokens=512,
                system=system,
                tools=ORDERING_TOOLS,
                messages=messages,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_calls[event.index] = {
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input_json": "",
                            }
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            text_chunk = event.delta.text
                            current_text += text_chunk
                            yield text_chunk
                        elif event.delta.type == "input_json_delta":
                            if event.index in current_tool_calls:
                                current_tool_calls[event.index]["input_json"] += event.delta.partial_json

                final_message = await stream.get_final_message()

            # Build the assistant content for history
            messages.append({"role": "assistant", "content": final_message.content})

            if final_message.stop_reason == "end_turn":
                break

            if final_message.stop_reason == "tool_use":
                tool_results = []
                for block in final_message.content:
                    if block.type == "tool_use":
                        logger.info(f"Tool call: {block.name}")
                        try:
                            tool_input = block.input
                        except Exception:
                            tool_input = {}

                        result = await tool_executor(
                            tool_name=block.name,
                            tool_input=tool_input,
                            session_id=self.session_id,
                            phone_number=self.phone_number,
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result) if not isinstance(result, str) else result,
                        })

                messages.append({"role": "user", "content": tool_results})
                # Continue the loop — the next response may have more text
                continue

            break

    async def clear_session(self) -> None:
        from app.redis_client import redis_delete
        await redis_delete(SESSION_KEY.format(session_id=self.session_id))
        await redis_delete(CART_KEY.format(session_id=self.session_id))
