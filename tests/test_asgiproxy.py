import pytest
from asgiref.testing import ApplicationCommunicator
from starlette.requests import Request

from asgiproxy.context import ProxyContext
from asgiproxy.simple_proxy import make_simple_proxy_app
from tests.configs import ExampleComProxyConfig
from tests.utils import http_response_from_asgi_messages, make_http_scope


@pytest.mark.parametrize("full_url, expected_url", [
    ("http://127.0.0.1/pathlet/?encode&flep&murp", "http://example.com/pathlet/?encode&flep&murp"),
    ("http://127.0.0.1/pathlet/", "http://example.com/pathlet/"),
])
def test_query_string_passthrough(full_url, expected_url):
    proxy_config = ExampleComProxyConfig()
    scope = make_http_scope(
        full_url=full_url,
        headers={
            "Accept": "text/html",
            "User-Agent": "Foo",
        },
    )
    client_request = Request(scope)
    opts = proxy_config.get_upstream_http_options(
        scope=scope, client_request=client_request, data=None
    )
    assert opts["url"] == expected_url


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
    app = make_simple_proxy_app(context, proxy_websocket_handler=None)

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
