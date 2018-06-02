from rain.ext.redis.base import BaseMix
from rain.ext.redis.utils import utf8, to_bytes


class HashMix(BaseMix):
	async def hdel(self, key, *fields):
		return await self.protocol.send(b'HDEL', key.encode(), *map(lambda x: x.encode(), fields))

	async def hexists(self, key, field):
		return await self.protocol.send(b'HEXISTS', key.encode(), field.encode())

	async def hget(self, key, field):
		return await self.protocol.send(b'HGET', key.encode(), field.encode())

	async def hset(self, key, field, val):
		return await self.protocol.send(b'HSET', key.encode(), field.encode(), utf8(val))

	async def hsetnx(self, key, field, val):
		return await self.protocol.send(b'HSETNX', key.encode(), field.encode(), utf8(val))

	async def hgetall(self, key):
		return await self.protocol.send(b'HGETALL', key.encode())

	async def hincrby(self, key, field, increment):
		return await self.protocol.send(b'HINCRBY', key.encode(), field.encode(), to_bytes(increment))

	async def hincrbyfloat(self, key, field, increment):
		return await self.protocol.send(b'HINCRBYFLOAT', key.encode(), field.encode(), to_bytes(increment))

	async def hkeys(self, key):
		return await self.protocol.send(b'HKEYS', key.encode())

	async def hlen(self, key):
		return await self.protocol.send(b'HLEN', key.encode())

	async def hmget(self, key, *fields):
		assert len(fields) > 0

		return await self.protocol.send(b'HMGET', key.encode(), map(lambda x: x.encode(), fields))

	async def hmset(self, key, *kvs):
		_ = len(kvs)
		assert _ > 0 and _ % 2 == 0

		return await self.protocol.send(
			b'HMSET',
			key.encode(),
			map(
				lambda x: x,
				*map(lambda x: x[1].encode() if x[0] % 2 == 0 else utf8(x[1]), enumerate(kvs))
			)
		)

	async def hvals(self, key):
		return await self.protocol.send(b'HVALS', key.encode())

	async def hscan(self, key, cursor=0, count=None, match=None):
		pass

	async def hstrlen(self, key, field):
		return await self.protocol.send(b'HSTRLEN', key.encode(), field.encode())
