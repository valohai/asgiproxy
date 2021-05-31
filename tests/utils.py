import gzip
from typing import List
from urllib.parse import urlparse

from asgiref.typing import HTTPScope
from starlette.datastructures import Headers


def http_response_from_asgi_messages(messages: List[dict]):
    start_message = next(m for m in messages if m["type"] == "http.response.start")
    body_bytes = b"".join(
        m.get("body", b"") for m in messages if m["type"] == "http.response.body"
    )
    headers = Headers(raw=start_message["headers"])
    if headers.get("content-encoding") == "gzip":
        content = gzip.decompress(body_bytes)
    else:
        content = body_bytes
    return {
        "status": start_message["status"],
        "headers": headers,
        "body": body_bytes,
        "content": content,
    }


def make_http_scope(*, method="GET", full_url: str, headers=None) -> HTTPScope:
    if headers is None:
        headers = {}
    headers = {str(key).lower(): str(value) for (key, value) in headers.items()}
    url_parts = urlparse(full_url)
    headers.setdefault("host", url_parts.netloc)
    # noinspection PyTypeChecker
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": url_parts.scheme,
        "path": url_parts.path,
        "raw_path": url_parts.path.encode(),
        "query_string": url_parts.query.encode(),
        "root_path": "/",
        "headers": [(key.encode(), value.encode()) for (key, value) in headers.items()],
        "extensions": {},
        "client": None,
        "server": None,
    }
