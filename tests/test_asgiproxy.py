import pytest
from asgiref.testing import ApplicationCommunicator

from asgiproxy.config import BaseURLProxyConfigMixin, ProxyConfig
from asgiproxy.context import ProxyContext
from asgiproxy.proxies.http import proxy_http
from tests.utils import http_response_from_asgi_messages


@pytest.mark.asyncio
async def test_asgiproxy():
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": "/",
        "query_string": "",
        "headers": [
            (b"Host", b"http://127.0.0.1/"),
            (b"User-Agent", b"Foo"),
            (b"Accept", b"text/html"),
        ],
    }

    class ExampleComProxyConfig(BaseURLProxyConfigMixin, ProxyConfig):
        upstream_base_url = "http://example.com"
        rewrite_host_header = "example.com"

    context = ProxyContext(config=ExampleComProxyConfig())

    async def app(scope, receive, send):
        return await proxy_http(
            context=context, scope=scope, receive=receive, send=send
        )

    async with context:
        acom = ApplicationCommunicator(app, scope)
        await acom.send_input({"type": "http.request", "body": b""})
        await acom.wait()
        messages = []
        while not acom.output_queue.empty():
            messages.append(await acom.receive_output())
        resp = http_response_from_asgi_messages(messages)
        assert resp["status"] == 200
        assert b"Example Domain" in resp["content"]
