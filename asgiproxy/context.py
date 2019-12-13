import asyncio

import aiohttp

from asgiproxy.config import ProxyConfig


class ProxyContext:
    semaphore: asyncio.Semaphore
    _session: aiohttp.ClientSession = None

    def __init__(self, config: ProxyConfig, max_concurrency=20):
        self.config = config
        self.semaphore = asyncio.Semaphore(max_concurrency)

    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession(
                cookie_jar=aiohttp.DummyCookieJar(), auto_decompress=False
            )
        return self._session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        if self._session:
            await self._session.close()
