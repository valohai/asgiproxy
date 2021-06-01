import asyncio

import aiohttp
import pytest
import uvicorn

from asgiproxy.context import ProxyContext
from asgiproxy.simple_proxy import make_simple_proxy_app
from tests.configs import ExampleComProxyConfig


@pytest.mark.asyncio
async def test_asgiproxy_e2e(unused_tcp_port):
    """
    End-to-end test the library's HTTP capabilities:

    * spin up a real Uvicorn server
    * send it a request using aiohttp
    * assert that we got the Example Domain response from example.com
    """
    port = unused_tcp_port
    context = ProxyContext(config=ExampleComProxyConfig())
    proxy_app = make_simple_proxy_app(context)
    cfg = uvicorn.Config(app=proxy_app, port=port, limit_max_requests=1)
    app = uvicorn.Server(config=cfg)
    async with context, aiohttp.ClientSession() as sess:

        async def request_soon():
            while not app.started:
                await asyncio.sleep(0.1)
            return await sess.request("GET", f"http://127.0.0.1:{port}/")

        _, resp = await asyncio.gather(app.serve(), request_soon())
        resp: aiohttp.ClientResponse
        assert resp.status == 200
        assert b"Example Domain" in await resp.read()
