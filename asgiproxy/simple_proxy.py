from starlette.types import ASGIApp, Receive, Scope, Send

from asgiproxy.context import ProxyContext
from asgiproxy.proxies.http import proxy_http
from asgiproxy.proxies.websocket import proxy_websocket


def make_simple_proxy_app(
    proxy_context: ProxyContext,
    *,
    proxy_http_handler=proxy_http,
    proxy_websocket_handler=proxy_websocket,
) -> ASGIApp:
    """
    Given a ProxyContext, return a simple ASGI application that can proxy
    HTTP and WebSocket connections.

    The handlers for the protocols can be overridden and/or removed with the
    respective parameters.
    """

    async def app(scope: Scope, receive: Receive, send: Send):  # noqa: ANN201
        if scope["type"] == "lifespan":
            return None  # We explicitly do nothing here for this simple app.

        if scope["type"] == "http" and proxy_http_handler:
            return await proxy_http_handler(
                context=proxy_context, scope=scope, receive=receive, send=send
            )

        if scope["type"] == "websocket" and proxy_websocket_handler:
            return await proxy_websocket_handler(
                context=proxy_context, scope=scope, receive=receive, send=send
            )

        raise NotImplementedError(f"Scope {scope} is not understood")

    return app
