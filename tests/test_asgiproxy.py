import pytest
from asgiref.testing import ApplicationCommunicator

from asgiproxy.context import ProxyContext
from asgiproxy.proxies.http import proxy_http
from tests.configs import ExampleComProxyConfig
from tests.utils import http_response_from_asgi_messages, make_http_scope


@pytest.mark.asyncio
async def test_asgiproxy():
    scope = make_http_scope(
        full_url="http://127.0.0.1/",
        headers={
            "Accept": "text/html",
            "User-Agent": "Foo",
        },
    )

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
