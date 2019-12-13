import argparse
import asyncio
from urllib.parse import urlparse

from asgiproxy.config import ProxyConfig, BaseURLProxyConfigMixin
from asgiproxy.context import ProxyContext
from asgiproxy.proxies.http import proxy_http
from asgiproxy.proxies.websocket import proxy_websocket

try:
    import uvicorn
except ImportError:
    uvicorn = None


def make_app(upstream_base_url):
    config = type(
        "Config",
        (BaseURLProxyConfigMixin, ProxyConfig),
        {
            "upstream_base_url": upstream_base_url,
            "rewrite_host_header": urlparse(upstream_base_url).netloc,
        },
    )()
    proxy_context = ProxyContext(config)

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            return  # We explicitly do nothing here for this simple app.

        if scope["type"] == "http":
            return await proxy_http(
                context=proxy_context, scope=scope, receive=receive, send=send
            )

        if scope["type"] == "websocket":
            return await proxy_websocket(
                context=proxy_context, scope=scope, receive=receive, send=send
            )

        raise NotImplementedError(f"Scope {scope} is not understood")

    return (app, proxy_context)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--port", type=int, default=40404)
    ap.add_argument("--host", type=str, default="0.0.0.0")
    args = ap.parse_args()
    if not uvicorn:
        ap.error(
            "The `uvicorn` ASGI server package is required for the command line client."
        )
    app, proxy_context = make_app(upstream_base_url=args.target)
    try:
        return uvicorn.run(host=args.host, port=int(args.port), app=app)
    finally:
        asyncio.run(proxy_context.close())


if __name__ == "__main__":
    main()
