from rain.ext.redis.base import BaseMix


class HashMix(BaseMix):
	async def hdel(self, key, *fields):
		return await self._send(b'HDEL', key, *fields)

	async def hexists(self, key, field):
		return await self._send(b'HEXISTS', key, field)

	async def hget(self, key, field):
		return await self._send(b'HGET', key, field)

	async def hset(self, key, field, val):
		return await self._send(b'HSET', key, field, val)

	async def hsetnx(self, key, field, val):
		return await self._send(b'HSETNX', key, field, val)

	async def hgetall(self, key):
		return await self._send(b'HGETALL', key)

	async def hincrby(self, key, field, increment):
		return await self._send(b'HINCRBY', key, field, increment)

	async def hincrbyfloat(self, key, field, increment):
		return await self._send(b'HINCRBYFLOAT', key, field, increment)

	async def hkeys(self, key):
		return await self._send(b'HKEYS', key)

	async def hlen(self, key):
		return await self._send(b'HLEN', key)

	async def hmget(self, key, *fields):
		assert len(fields) > 0

		return await self._send(b'HMGET', key, *fields)

	async def hmset(self, key, *kvs):
		_ = len(kvs)
		assert _ > 0 and _ % 2 == 0

		return await self._send(b'HMSET', key, *kvs)

	async def hvals(self, key):
		return await self._send(b'HVALS', key)

	async def hscan(self, key, cursor=0, count=None, match=None):
		pass

	async def hstrlen(self, key, field):
		return await self._send(b'HSTRLEN', key, field)
