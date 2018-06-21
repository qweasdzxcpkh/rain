from rain.ext.redis.base import BaseMix


class ListMix(BaseMix):
	async def lindex(self, key, index):
		return await self._send(b'LINDEX', key, index)

	async def linsert(self, key, pivot, val, before=False):
		return await self._send(
			b'LINSERT', key, b'BEFORE' if before else b'AFTER', pivot, val
		)

	async def llen(self, key):
		return await self._send(b'LLEN', key)

	async def lpop(self, key):
		return await self._send(b'LPOP', key)

	async def rpop(self, key):
		return await self._send(b'RPOP', key)

	async def lpush(self, key, *vals):
		return await self._send(b'LPUSH', key, *vals)

	async def rpush(self, key, *vals):
		return await self._send(b'RPUSH', key, *vals)

	async def lpushx(self, key, val):
		return await self._send(b'LPUSHX', key, val)

	async def rpushx(self, key, val):
		return await self._send(b'RPUSHX', key, val)

	async def lrange(self, key, start, stop):
		return await self._send(b'LRANGE', key, start, stop)

	async def lrem(self, key, count, val):
		return await self._send(b'LREM', key, count, val)

	async def lset(self, key, index, val):
		return await self._send(b'LSET', key, index, val)

	async def ltrim(self, key, start, stop):
		return await self._send(b'LTRIM', key, start, stop)
