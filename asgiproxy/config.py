from typing import Union, Optional
from urllib.parse import urljoin

import aiohttp
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.types import Scope
from starlette.websockets import WebSocket

Headerlike = Union[dict, Headers]


class ProxyConfig:
    def get_upstream_url(self, *, scope: Scope) -> str:
        """
        Get the upstream URL for a client request.
        """
        raise NotImplementedError("...")

    def process_client_headers(self, *, scope: Scope, headers: Headers) -> Headerlike:
        """
        Process client HTTP headers before they're passed upstream.
        """
        return headers

    def process_upstream_headers(
        self, *, scope: Scope, proxy_response: aiohttp.ClientResponse
    ) -> Headerlike:
        """
        Process upstream HTTP headers before they're passed to the client.
        """
        return proxy_response.headers

    def get_upstream_http_options(
        self, *, scope: Scope, client_request: Request, data
    ) -> dict:
        """
        Get request options (as passed to aiohttp.ClientSession.request).
        """
        return dict(
            method=client_request.method,
            url=self.get_upstream_url(scope=scope),
            params=client_request.query_params.multi_items(),
            data=data,
            headers=self.process_client_headers(
                scope=scope, headers=client_request.headers
            ),
            allow_redirects=False,
        )

    def get_upstream_websocket_options(
        self, *, scope: Scope, client_ws: WebSocket
    ) -> dict:
        """
        Get websocket connection options (as passed to aiohttp.ClientSession.ws_connect).
        """
        return dict(
            method=scope.get("method", "GET"),
            url=self.get_upstream_url(scope=scope),
            headers=self.process_client_headers(scope=scope, headers=client_ws.headers),
        )


class BaseURLProxyConfigMixin:
    upstream_base_url: str
    rewrite_host_header: Optional[str] = None

    def get_upstream_url(self, scope: Scope) -> str:
        return urljoin(self.upstream_base_url, scope["path"])

    def process_client_headers(
        self, *, scope: Scope, headers: Headerlike
    ) -> Headerlike:
        """
        Process client HTTP headers before they're passed upstream.
        """
        if self.rewrite_host_header:
            headers = headers.mutablecopy()
            headers["host"] = self.rewrite_host_header
        return super().process_client_headers(scope=scope, headers=headers)
