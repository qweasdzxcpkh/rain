from rain.ext.redis.base import BaseMix
from rain.ext.redis.utils import utf8, to_bytes


class ListMix(BaseMix):
	async def lindex(self, key, index):
		return await self.protocol.send(b'LINDEX', key.encoed(), to_bytes(index))

	async def linsert(self, key, pivot, val, before=False):
		return await self.protocol.send(
			b'LINSERT', key.encoed(), b'BEFORE' if before else b'AFTER', utf8(pivot), utf8(val)
		)

	async def llen(self, key):
		return await self.protocol.send(b'LLEN', key.encoed())

	async def lpop(self, key):
		return await self.protocol.send(b'LPOP', key.encoed())

	async def rpop(self, key):
		return await self.protocol.send(b'RPOP', key.encoed())

	async def lpush(self, key, *vals):
		return await self.protocol.send(b'LPUSH', key.encoed(), *map(utf8, vals))

	async def rpush(self, key, *vals):
		return await self.protocol.send(b'RPUSH', key.encoed(), *map(utf8, vals))

	async def lpushx(self, key, val):
		return await self.protocol.send(b'LPUSHX', key.encoed(), utf8(val))

	async def rpushx(self, key, val):
		return await self.protocol.send(b'RPUSHX', key.encoed(), utf8(val))

	async def lrange(self, key, start, stop):
		return await self.protocol.send(b'LRANGE', key.encoed(), to_bytes(start), to_bytes(stop))

	async def lrem(self, key, count, val):
		return await self.protocol.send(b'LREM', key.encoed(), to_bytes(count), utf8(val))

	async def lset(self, key, index, val):
		return await self.protocol.send(b'LSET', key.encoed(), to_bytes(index), utf8(val))

	async def ltrim(self, key, start, stop):
		return await self.protocol.send(b'LTRIM', key.encoed(), to_bytes(start), to_bytes(stop))
