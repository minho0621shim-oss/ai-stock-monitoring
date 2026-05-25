import asyncio
import json
import logging
import time
from typing import Callable, Dict, Any

import websockets

logger = logging.getLogger(__name__)

class SamsungWSClient:
    """
    Singleton class for Samsung Securities OpenAPI WebSocket connection.
    Features:
    - Auto-reconnection on drop
    - Token (approval_key) refresh
    - Singleton pattern to prevent multiple connections
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SamsungWSClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._initialized = True
        self.app_key = "" # Set via env vars or config
        self.app_secret = ""
        # Samsung Securities OpenAPI WS URL
        self.ws_url = "ws://ops.samsungpop.com:21000" # NOTE: Check exact URL in Samsung API docs
        self.approval_key = None
        self.token_expiry = 0
        self.ws = None
        self.is_connected = False
        self.reconnect_delay = 3
        self.callbacks: Dict[str, Callable] = {}
        self._reconnect_task = None
        self._listen_task = None

    async def get_approval_key(self):
        """
        Fetches the WebSocket approval key.
        In a real scenario, this makes a POST request to the OpenAPI REST endpoint.
        """
        logger.info("Fetching new Samsung OpenAPI approval key...")
        # TODO: Implement actual REST API request using httpx or requests
        # Example:
        # response = await httpx.post("https://openapi.samsungpop.com/oauth2/Approval", json={"grant_type":"client_credentials", "appkey":self.app_key, "secretkey":self.app_secret})
        # data = response.json()
        # self.approval_key = data.get("approval_key")
        
        await asyncio.sleep(1) # Mocking network delay
        self.approval_key = "MOCK_APPROVAL_KEY"
        self.token_expiry = time.time() + 86000 # Keys usually last ~24 hours
        
    async def connect(self):
        if not self.approval_key or time.time() >= self.token_expiry:
            await self.get_approval_key()

        try:
            logger.info(f"Connecting to {self.ws_url}...")
            self.ws = await websockets.connect(self.ws_url, ping_interval=30)
            self.is_connected = True
            logger.info("Samsung WebSocket Connected.")
            
            # Resubscribe to previous topics upon reconnect
            await self._resubscribe()

            if self._listen_task is None or self._listen_task.done():
                self._listen_task = asyncio.create_task(self._listen())
                
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.is_connected = False
            await self.schedule_reconnect()

    async def _listen(self):
        try:
            async for message in self.ws:
                self._handle_message(message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Samsung WebSocket closed: {e}")
        except Exception as e:
            logger.error(f"Samsung WebSocket listen error: {e}")
        finally:
            self.is_connected = False
            await self.schedule_reconnect()

    def _handle_message(self, message: str):
        """
        Parse incoming messages and route them to registered callbacks.
        """
        # Samsung API typically sends pipe-separated values or JSON
        # Assuming JSON for structure here; adapt based on specific TR ID specs
        try:
            # Some responses might be plain text, this depends on Samsung's spec
            if message.startswith('{'):
                data = json.loads(message)
                tr_id = data.get("header", {}).get("tr_id")
                if tr_id in self.callbacks:
                    self.callbacks[tr_id](data)
            else:
                # Handle pipe-separated real-time data
                parts = message.split('|')
                # Usually parts[0] or parts[1] is the TR ID or symbol
                tr_id = parts[0] if parts else ""
                if tr_id in self.callbacks:
                    self.callbacks[tr_id](parts)
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def schedule_reconnect(self):
        if self._reconnect_task and not self._reconnect_task.done():
            return
        
        async def reconnect_routine():
            logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
            await asyncio.sleep(self.reconnect_delay)
            await self.connect()
            
        self._reconnect_task = asyncio.create_task(reconnect_routine())

    async def subscribe(self, tr_id: str, tr_key: str, callback: Callable):
        """
        Subscribe to a specific TR ID and stock code (tr_key).
        """
        sub_key = f"{tr_id}_{tr_key}"
        self.callbacks[sub_key] = callback
        
        if self.is_connected and self.ws:
            msg = self._build_subscribe_msg(tr_id, tr_key, "1") # "1" for register
            await self.ws.send(json.dumps(msg))

    async def _resubscribe(self):
        """Resubscribe to all active topics after a reconnect."""
        for key in self.callbacks.keys():
            try:
                tr_id, tr_key = key.split('_', 1)
                msg = self._build_subscribe_msg(tr_id, tr_key, "1")
                await self.ws.send(json.dumps(msg))
            except Exception as e:
                logger.error(f"Error resubscribing to {key}: {e}")

    def _build_subscribe_msg(self, tr_id: str, tr_key: str, tr_type: str) -> dict:
        return {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P", # Personal
                "tr_type": tr_type, # 1: Sub, 2: Unsub
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": tr_key
                }
            }
        }

    async def close(self):
        if self.ws:
            await self.ws.close()
        self.is_connected = False
        if self._listen_task:
            self._listen_task.cancel()
        if self._reconnect_task:
            self._reconnect_task.cancel()

# Example usage:
# async def main():
#     client = SamsungWSClient()
#     await client.connect()
#     await client.subscribe("H0STCNT0", "005930", lambda msg: print(f"Update: {msg}"))
#     await asyncio.sleep(60)
#     await client.close()
