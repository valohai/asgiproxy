import gzip
from typing import List

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
