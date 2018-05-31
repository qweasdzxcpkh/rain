from rain.ext.redis.base import BaseMix
from rain.ext.redis.utils import utf8, to_bytes


class StringMix(BaseMix):
	async def append(self, key, val):
		return await self.protocol.send(b'APPEND', key.encode(), utf8(val))

	async def get(self, key):
		return await self.protocol.send(b'GET', key.encode())

	async def set(self, key, val, ex=None, px=None):
		_ = []
		if ex:
			if px:
				_ += [b'PX', px]
			else:
				_ += [b'EX', ex]

		return await self.protocol.send(b'SET', key.encode(), utf8(val), *_)

	async def bitcount(self, key, start=None, end=None):
		_ = []
		if start is not None and end is not None:
			_ += [to_bytes(start), to_bytes(end)]

		return await self.protocol.send(b'BITCOUNT', key.encode(), *_)

	async def bitop(self, operation, destkey, *keys):
		operation = operation.upper()
		assert operation in {'AND', 'OR', 'XOR', 'NOT'}
		assert len(keys) > 0
		if operation == 'NOT':
			keys = keys[0:1]

		return await self.protocol.send(b'BITOP', operation.encode(), destkey.encode(), *keys)

	async def bitfield(self):
		pass

	async def decr(self, key):
		return await self.protocol.send(b'DECR', key.encode())

	async def decrby(self, key, decrement):
		return await self.protocol.send(b'DECRBY', key.encode(), to_bytes(decrement))

	async def getbit(self, key, offset):
		return await self.protocol.send(b'GETBIT', key.encode(), to_bytes(offset))

	async def getrange(self, key, start, end):
		return await self.protocol.send(b'GETRANGE', key.encode(), to_bytes(start), to_bytes(end))

	async def getset(self, key, val):
		return await self.protocol.send(b'GETSET', key.encode(), utf8(val))

	async def incr(self, key):
		return await self.protocol.send(b'INCR', key.encode())

	async def incrby(self, key, increment):
		return await self.protocol.send(b'INCRBY', key.encode(), to_bytes(increment))

	async def incrbyfloat(self, key, increment):
		return await self.protocol.send(b'INCRBYFLOAT', key.encode(), to_bytes(increment))

	async def mget(self, *keys):
		assert len(keys) > 0
		return await self.protocol.send(b'MGET', *map(lambda x: x.encode(), keys))

	async def mset(self, *kvs):
		_ = len(kvs)
		assert _ > 0 and _ % 2 == 0

		return await self.protocol.send(
			b'MSET',
			*map(lambda x: x[1].encode() if x[0] % 2 == 0 else utf8(x[1]), enumerate(kvs))
		)

	async def msetnx(self, *kvs):
		_ = len(kvs)
		assert _ > 0 and _ % 2 == 0

		return await self.protocol.send(
			b'MSETNX',
			*map(lambda x: x[1].encode() if x[0] % 2 == 0 else utf8(x[1]), enumerate(kvs))
		)

	async def setex(self, key, seconds, val):
		return await self.protocol.send(b'SETEX', key.encode(), to_bytes(seconds), utf8(val))

	async def setnx(self, key, val):
		return await self.protocol.send(b'SETNX', key.encode(), utf8(val))

	async def psetex(self, key, milliseconds, val):
		return await self.protocol.send(b'PSETEX', key.encode(), to_bytes(milliseconds), utf8(val))

	async def setbit(self, key, offset, val):
		return await self.protocol.send(b'SETBIT', key.encode(), to_bytes(offset), to_bytes(val))

	async def setrange(self, key, offset, val):
		return await self.protocol.send(b'SETRANGE', key.encode(), to_bytes(offset), to_bytes(val))

	async def strlen(self, key):
		return await self.protocol.send(b'STRLEN', key.encode())
