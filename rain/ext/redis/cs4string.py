from rain.ext.redis.base import BaseMix


class StringMix(BaseMix):
	async def append(self, key, val):
		return await self.protocol.send(b'APPEND', key, val)

	async def get(self, key):
		return await self.protocol.send(b'GET', key)

	async def get_string(self, key):
		_ = await self.get(key)
		return _.decode()

	async def get_int(self, key):
		_ = await self.get(key)
		return int(_)

	async def set(self, key, val, ex=None, px=None):
		_ = []
		if ex:
			if px:
				_ += [b'PX', px]
			else:
				_ += [b'EX', ex]

		return await self.protocol.send(b'SET', key, val, *_)

	async def bitcount(self, key, start=None, end=None):
		_ = []
		if start is not None and end is not None:
			_ += [start, end]

		return await self.protocol.send(b'BITCOUNT', key, *_)

	async def bitop(self, operation, destkey, *keys):
		operation = operation.upper()
		assert operation in {'AND', 'OR', 'XOR', 'NOT'}
		assert len(keys) > 0
		if operation == 'NOT':
			keys = keys[0:1]

		return await self.protocol.send(b'BITOP', operation, destkey, *keys)

	async def bitfield(self):
		pass

	async def decr(self, key):
		return await self.protocol.send(b'DECR', key)

	async def decrby(self, key, decrement):
		return await self.protocol.send(b'DECRBY', key, decrement)

	async def getbit(self, key, offset):
		return await self.protocol.send(b'GETBIT', key, offset)

	async def getrange(self, key, start, end):
		return await self.protocol.send(b'GETRANGE', key, start, end)

	async def getset(self, key, val):
		return await self.protocol.send(b'GETSET', key, val)

	async def incr(self, key):
		return await self.protocol.send(b'INCR', key)

	async def incrby(self, key, increment):
		return await self.protocol.send(b'INCRBY', key, increment)

	async def incrbyfloat(self, key, increment):
		return await self.protocol.send(b'INCRBYFLOAT', key, increment)

	async def mget(self, *keys):
		assert len(keys) > 0
		return await self.protocol.send(b'MGET', keys)

	async def mset(self, *kvs):
		_ = len(kvs)
		assert _ > 0 and _ % 2 == 0

		return await self.protocol.send(b'MSET', kvs)

	async def msetnx(self, *kvs):
		_ = len(kvs)
		assert _ > 0 and _ % 2 == 0

		return await self.protocol.send(b'MSETNX', kvs)

	async def setex(self, key, seconds, val):
		return await self.protocol.send(b'SETEX', key, seconds, val)

	async def setnx(self, key, val):
		return await self.protocol.send(b'SETNX', key, val)

	async def psetex(self, key, milliseconds, val):
		return await self.protocol.send(b'PSETEX', key, milliseconds, val)

	async def setbit(self, key, offset, val):
		return await self.protocol.send(b'SETBIT', key, offset, val)

	async def setrange(self, key, offset, val):
		return await self.protocol.send(b'SETRANGE', key, offset, val)

	async def strlen(self, key):
		return await self.protocol.send(b'STRLEN', key)
