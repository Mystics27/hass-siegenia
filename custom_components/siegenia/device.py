"""Siegenia device communication."""
from __future__ import annotations

import asyncio
import json
import logging
import ssl
from typing import Any, Callable

import aiohttp
from aiohttp import ClientSession, ClientWebSocketResponse

from .const import WS_HEARTBEAT_INTERVAL, WS_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class SiegeniaDevice:
    """Siegenia device WebSocket client."""

    def __init__(
        self,
        host: str,
        port: int = 443,
        username: str = "admin",
        password: str = "0000",
        use_ssl: bool = True,
    ) -> None:
        """Initialize the device."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        
        self._session: ClientSession | None = None
        self._websocket: ClientWebSocketResponse | None = None
        self._request_id = 0
        self._awaiting_responses: dict[int, asyncio.Future] = {}
        self._heartbeat_task: asyncio.Task | None = None
        self._token: str | None = None
        self._device_info: dict[str, Any] = {}
        self._data_callback: Callable[[dict[str, Any]], None] | None = None

    @property
    def is_connected(self) -> bool:
        """Return if device is connected."""
        return self._websocket is not None and not self._websocket.closed

    async def connect(self) -> None:
        """Connect to the device."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        protocol = "wss" if self.use_ssl else "ws"
        url = f"{protocol}://{self.host}:{self.port}/WebSocket"
        
        # SSL context that accepts self-signed certificates
        ssl_context = None
        if self.use_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            self._websocket = await self._session.ws_connect(
                url,
                ssl=ssl_context,
                origin=f"{protocol}://{self.host}:{self.port}",
                timeout=aiohttp.ClientTimeout(total=WS_TIMEOUT),
                headers={"User-Agent": "Home Assistant Siegenia Integration"}
            )
            
            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Start message listener
            asyncio.create_task(self._listen_for_messages())
            
            _LOGGER.info("Connected to Siegenia device at %s:%s", self.host, self.port)
            
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Failed to connect to %s:%s - %s", self.host, self.port, err)
            await self.disconnect()
            raise ConnectionError(f"Cannot connect to {self.host}:{self.port}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error connecting to %s:%s - %s", self.host, self.port, err)
            await self.disconnect()
            raise

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

        if self._websocket and not self._websocket.closed:
            await self._websocket.close()
            
        if self._session:
            await self._session.close()
            self._session = None
            
        self._websocket = None
        self._token = None

    async def login(self) -> bool:
        """Login to the device."""
        try:
            request = {
                "command": "login",
                "user": self.username,
                "password": self.password,
                "long_life": False,
                "id": self._get_next_request_id()
            }
            
            # Create future for response
            future = asyncio.Future()
            self._awaiting_responses[request["id"]] = future

            # Send request
            await self._websocket.send_str(json.dumps(request))
            _LOGGER.debug("Sent login request: %s", json.dumps(request))
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=WS_TIMEOUT)
            
            if response.get("status") == "ok" and "data" in response:
                self._token = response["data"].get("token")
                _LOGGER.info("Successfully logged in to device %s", self.host)
                return True
            else:
                _LOGGER.error("Login failed: %s", response.get("status", "Unknown error"))
                return False
                
        except Exception as err:
            _LOGGER.error("Login error: %s", err)
            return False

    async def get_device_info(self) -> dict[str, Any]:
        """Get device information."""
        response = await self._send_request("getDevice")
        if response.get("status") == "ok" and "data" in response:
            self._device_info = response["data"]
            return self._device_info
        return {}

    async def get_device_params(self) -> dict[str, Any]:
        """Get device parameters."""
        response = await self._send_request("getDeviceParams")
        if response.get("status") == "ok" and "data" in response:
            return response["data"]
        return {}

    async def get_device_state(self) -> dict[str, Any]:
        """Get device state."""
        response = await self._send_request("getDeviceState")
        if response.get("status") == "ok" and "data" in response:
            return response["data"]
        return {}

    async def set_device_active(self, active: bool) -> bool:
        """Turn device on/off."""
        params = {"devicestate": {"deviceactive": active}}
        response = await self._send_request("setDeviceParams", params)
        return response.get("status") == "ok"

    async def set_fan_level(self, level: int) -> bool:
        """Set fan level (0-7)."""
        if not 0 <= level <= 7:
            raise ValueError("Fan level must be between 0 and 7")
            
        params = {"fanlevel": level}
        response = await self._send_request("setDeviceParams", params)
        return response.get("status") == "ok"

    def set_data_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Set callback for data updates."""
        self._data_callback = callback

    def _get_next_request_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    async def _send_request(self, command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a request to the device."""
        if not self.is_connected:
            raise ConnectionError("Not connected to device")

        request_id = self._get_next_request_id()
        request = {
            "command": command,
            "id": request_id
        }
        
        if params:
            request["params"] = params

        # Create future for response
        future = asyncio.Future()
        self._awaiting_responses[request_id] = future

        try:
            # Send request
            await self._websocket.send_str(json.dumps(request))
            _LOGGER.debug("Sent request: %s", json.dumps(request))
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=WS_TIMEOUT)
            return response
            
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout waiting for response to request %s", request_id)
            if request_id in self._awaiting_responses:
                del self._awaiting_responses[request_id]
            raise
        except Exception as err:
            _LOGGER.error("Error sending request: %s", err)
            if request_id in self._awaiting_responses:
                del self._awaiting_responses[request_id]
            raise

    async def _listen_for_messages(self) -> None:
        """Listen for incoming WebSocket messages."""
        try:
            async for msg in self._websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        _LOGGER.debug("Received message: %s", json.dumps(data))
                        await self._handle_message(data)
                    except json.JSONDecodeError as err:
                        _LOGGER.error("Failed to decode message: %s - Raw: %s", err, msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.error("WebSocket error: %s", self._websocket.exception())
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    _LOGGER.info("WebSocket connection closed")
                    break
        except Exception as err:
            _LOGGER.error("Error in message listener: %s", err)

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """Handle incoming WebSocket message."""
        message_id = data.get("id")
        
        # Handle response to our request
        if message_id and message_id in self._awaiting_responses:
            future = self._awaiting_responses.pop(message_id)
            if not future.done():
                future.set_result(data)
        # Handle unsolicited data updates
        elif data.get("command") == "deviceParams" and self._data_callback:
            self._data_callback(data.get("data", {}))

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat to keep connection alive."""
        while self.is_connected:
            try:
                await asyncio.sleep(WS_HEARTBEAT_INTERVAL)
                if self.is_connected:
                    await self._send_request("keepAlive", {"extend_session": True})
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.error("Heartbeat error: %s", err)
                break