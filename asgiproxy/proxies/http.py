import aiohttp
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import Receive, Scope, Send

from asgiproxy.context import ProxyContext
from asgiproxy.utils.streams import read_stream_in_chunks

# TODO: make these configurable?
INCOMING_STREAMING_THRESHOLD = 512 * 1024
OUTGOING_STREAMING_THRESHOLD = 1024 * 1024 * 5


def determine_incoming_streaming(request) -> bool:
    if request.method in ("GET", "HEAD"):
        return False

    try:
        return int(request.headers["content-length"]) < INCOMING_STREAMING_THRESHOLD
    except (TypeError, ValueError, KeyError):
        # Malformed or missing content-length header; assume a very large payload
        return True


def determine_outgoing_streaming(proxy_response: aiohttp.ClientResponse) -> bool:
    if proxy_response.status != 200:
        return False
    try:
        return (
            int(proxy_response.headers["content-length"]) > OUTGOING_STREAMING_THRESHOLD
        )
    except (TypeError, ValueError, KeyError):
        # Malformed or missing content-length header; assume a streaming payload
        return True


async def get_proxy_response(
    *, context: ProxyContext, scope: Scope, receive: Receive
) -> aiohttp.ClientResponse:
    request = Request(scope, receive)
    should_stream_incoming = determine_incoming_streaming(request)
    async with context.semaphore:
        if request.method not in ("GET", "HEAD"):
            if should_stream_incoming:
                data = request.stream()
            else:
                data = await request.body()
        else:
            data = None

        kwargs = context.config.get_upstream_http_options(
            scope=scope, client_request=request, data=data
        )

        proxy_response = await context.session.request(**kwargs)
    return proxy_response


async def convert_proxy_response_to_user_response(
    *, context: ProxyContext, scope: Scope, proxy_response: aiohttp.ClientResponse
) -> Response:
    should_stream_outgoing = determine_outgoing_streaming(proxy_response)
    headers_to_client = context.config.process_upstream_headers(
        scope=scope, proxy_response=proxy_response
    )
    response_kwargs = dict(status_code=proxy_response.status, headers=headers_to_client)
    if should_stream_outgoing:
        user_response = StreamingResponse(
            content=read_stream_in_chunks(proxy_response.content), **response_kwargs
        )
    else:
        user_response = Response(content=await proxy_response.read(), **response_kwargs)
    return user_response


async def proxy_http(
    *, context: ProxyContext, scope: Scope, receive: Receive, send: Send
):
    proxy_response = await get_proxy_response(
        context=context, scope=scope, receive=receive
    )
    user_response = await convert_proxy_response_to_user_response(
        context=context, scope=scope, proxy_response=proxy_response
    )
    return await user_response(scope, receive, send)
