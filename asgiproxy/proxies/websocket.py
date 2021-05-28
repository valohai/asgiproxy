import asyncio
import logging
import uuid
from typing import Optional

from aiohttp import ClientWebSocketResponse, WSMessage, WSMsgType
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket
from websockets.exceptions import ConnectionClosed

from asgiproxy.context import ProxyContext

log = logging.getLogger(__name__)


class UnknownMessage(ValueError):
    pass


class WebSocketProxyContext:
    def __init__(
        self,
        *,
        id: str = None,
        client_ws: WebSocket,
        upstream_ws: ClientWebSocketResponse,
    ) -> None:
        self.id = str(id or uuid.uuid4())
        self.client_ws = client_ws
        self.upstream_ws = upstream_ws

    async def client_to_upstream_loop(self):
        while True:
            client_msg: dict = await self.client_ws.receive()
            if client_msg["type"] == "websocket.disconnect":
                log.info(f"WSP {self.id}: Client closed connection.")
                return
            log.debug(f"C->U: {client_msg}")
            await self.send_client_to_upstream(client_msg)

    async def send_client_to_upstream(self, client_msg: dict):
        if client_msg.get("text"):
            await self.upstream_ws.send_str(client_msg["text"])
            return True

        if client_msg.get("bytes"):
            await self.upstream_ws.send_bytes(client_msg["bytes"])
            return True

        raise UnknownMessage(
            f"WSP {self.id}: Unknown client WS message: {client_msg}", client_msg
        )

    async def send_upstream_to_client(self, upstream_msg: WSMessage):
        if upstream_msg.type == WSMsgType.text:
            await self.client_ws.send_text(upstream_msg.data)
            return
        if upstream_msg.type == WSMsgType.binary:
            await self.client_ws.send_bytes(upstream_msg.data)
            return
        raise UnknownMessage(
            f"WSP {self.id}: Unknown upstream WS message: {upstream_msg}", upstream_msg
        )

    async def upstream_to_client_loop(self):
        while True:
            upstream_msg: WSMessage = await self.upstream_ws.receive()
            log.debug(f"WSP {self.id}: U->C: {upstream_msg}")

            if upstream_msg.type == WSMsgType.closed:
                log.info(f"WSP {self.id}: Upstream closed connection.")
                return

            try:
                await self.send_upstream_to_client(upstream_msg=upstream_msg)
            except ConnectionClosed as cc:
                log.info(
                    f"WSP {self.id}: Upstream-to-client loop: client connection had closed ({cc})."
                )
                return

    async def loop(self):
        log.debug(f"WSP {self.id}: Starting main loop.")
        ctu_task = asyncio.create_task(self.client_to_upstream_loop())
        utc_task = asyncio.create_task(self.upstream_to_client_loop())
        try:
            await asyncio.wait(
                [ctu_task, utc_task], return_when=asyncio.FIRST_COMPLETED
            )
            ctu_task.cancel()
            utc_task.cancel()
        except Exception:
            log.warning(f"WSP {self.id}: Unexpected exception!", exc_info=True)
            raise
        log.debug(f"WSP {self.id}: Ending main loop.")


async def proxy_websocket(
    *, context: ProxyContext, scope: Scope, receive: Receive, send: Send
) -> None:
    client_ws: Optional[WebSocket] = None
    upstream_ws: Optional[ClientWebSocketResponse] = None
    try:
        client_ws = WebSocket(scope=scope, receive=receive, send=send)
        await client_ws.accept()
        async with context.session.ws_connect(
            **context.config.get_upstream_websocket_options(
                scope=scope, client_ws=client_ws
            )
        ) as upstream_ws:
            ctx = WebSocketProxyContext(client_ws=client_ws, upstream_ws=upstream_ws)
            await ctx.loop()
    finally:
        if upstream_ws:
            try:
                await upstream_ws.close()
            except Exception:
                pass
        if client_ws:
            try:
                await client_ws.close()
            except Exception:
                pass
