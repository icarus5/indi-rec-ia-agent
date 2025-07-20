import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import os
from typing import Any, Dict
import redis
from src.integrations.indi.provider import IndiProvider
from src.utils.date.date_utils import get_date


class AggregatorService:
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv("REDIS_INDIBOT"), decode_responses=True)
        self.indi_provider = IndiProvider()
        self.redis_prefix = "whatsapp_buffer"
        self.wait_time = int(os.getenv("MESSAGE_BUFFER_WAIT_TIME"))
        self.user_tasks: Dict[str, asyncio.Task] = {}
        self.user_futures: Dict[str, asyncio.Future] = {}
        self.lock = asyncio.Lock()
    
    async def buffer_message(self, user_id: str, incoming_message: str, incoming_type: str, incoming_mediaUrl: str = ''):
        now = get_date().isoformat()
        user_key = f"{self.redis_prefix}:{user_id}"
        raw = self.redis_client.get(user_key)
        incoming_ocr_context = False
        incoming_ocr_success_status = True

        try:
            current_state = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            current_state = {}
        if incoming_type == 'IMAGE':
            incoming_ocr_success_status = incoming_message.get("success", True)
            incoming_ocr_context = incoming_message.get("ocr_context", False)
            incoming_message = incoming_message['message']
            
        current_failure_status = current_state.get("internal_failure", False)
        current_buffer = current_state.get("message_buffer", "")
        current_listed_buffer = current_state.get("listed_buffer", {})
        updated_buffer = (current_buffer.strip() + " " + incoming_message.strip()).strip()
        message_payload = {
            'message': incoming_ocr_context if incoming_ocr_success_status == False else incoming_message,
            'type': incoming_type,
            'mediaUrl': incoming_mediaUrl,
            'ocr_context' : incoming_ocr_context if incoming_ocr_context else None,
            'ocr_success_status': incoming_ocr_success_status
        }
        current_listed_buffer[now] = message_payload

        if current_failure_status == False:
            new_state = {
                "message_buffer": updated_buffer,
                "message_buffer_ts": now,
                "listed_buffer": current_listed_buffer
            }
        else:
            new_state = current_state

        if incoming_ocr_success_status == False:
            new_state['internal_failure'] = True
            new_state['internal_failure_context'] = incoming_ocr_context if incoming_ocr_context else None
            new_state['message_buffer'] = incoming_message.strip()

        self.redis_client.set(user_key, json.dumps(new_state))

    async def aggregate_if_ready(self, user_id: str) -> dict:
        await asyncio.sleep(self.wait_time)

        user_key = f"{self.redis_prefix}:{user_id}"
        raw = self.redis_client.get(user_key)
        if not raw:
            return {"status": "waiting", "message": None}

        state = json.loads(raw)

        final_message = state.get("message_buffer", "").strip()
        final_list = state.get("listed_buffer", {})
        final_failure_check = state.get("internal_failure", False)
        final_failure_input = state.get("internal_failure_context", '')

        self.redis_client.delete(user_key)

        if final_failure_check:
            return {"status": "interal_failure", "message": final_message, "failure_input": final_failure_input, "listed_messages": final_list}
        else:
            return {"status": "complete", "message": final_message, "listed_messages": final_list}


