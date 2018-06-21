from rain.ext.redis.base import BaseMix


class HyperLogLogMix(BaseMix):
	async def pfadd(self, key, *items):
		assert items
		return await self._send(b'PFADD', key, *items)

	async def pfcount(self, *keys):
		assert keys
		return await self._send(b'PFCOUNT', *keys)

	async def pfmerge(self, destkey, *source_keys):
		assert source_keys
		return await self._send(b'PFMERGE', destkey, *source_keys)
