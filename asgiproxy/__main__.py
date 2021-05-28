import argparse
import asyncio
from typing import Tuple
from urllib.parse import urlparse

from starlette.types import ASGIApp

from asgiproxy.config import BaseURLProxyConfigMixin, ProxyConfig
from asgiproxy.context import ProxyContext
from asgiproxy.simple_proxy import make_simple_proxy_app

try:
    import uvicorn
except ImportError:
    uvicorn = None


def make_app(upstream_base_url: str) -> Tuple[ASGIApp, ProxyContext]:
    config = type(
        "Config",
        (BaseURLProxyConfigMixin, ProxyConfig),
        {
            "upstream_base_url": upstream_base_url,
            "rewrite_host_header": urlparse(upstream_base_url).netloc,
        },
    )()
    proxy_context = ProxyContext(config)
    app = make_simple_proxy_app(proxy_context)
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
