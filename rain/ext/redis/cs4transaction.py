from rain.ext.redis.base import BaseMix


class Transaction(BaseMix):
	async def discard(self):
		return await self._send(b'DISCARD')

	async def exec(self):
		return await self._send(b'EXEC')

	async def multi(self):
		return await self._send(b'MULTI')

	async def unwatch(self):
		return await self._send(b'UNWATCH')

	async def watch(self, *keys):
		assert keys
		return await self._send(b'WATCH', *keys)
