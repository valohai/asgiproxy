import asyncio
from typing import Union

import aiohttp

Streamable = Union[asyncio.StreamReader, aiohttp.StreamReader]


async def read_stream_in_chunks(stream: Streamable, chunk_size: int = 524_288):
    while True:
        chunk = await stream.read(chunk_size)
        yield chunk
        if not chunk:
            break
