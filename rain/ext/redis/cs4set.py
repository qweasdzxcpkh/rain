from rain.ext.redis.base import BaseMix
from rain.ext.redis.utils import utf8, to_bytes


class SetMix(BaseMix):
	async def sadd(self, key, *members):
		return await self.protocol.send(b'SADD', key.encode(), *map(utf8, members))

	async def scadd(self, key):
		return await self.protocol.send(b'SCADD', key.encode())

	async def sdiff(self, key, *other_keys):
		return await self.protocol.send(b'SDIFF', key.encode(), *map(lambda x: x.encode(), other_keys))

	async def sdiffstore(self, destination, key, *other_keys):
		return await self.protocol.send(
			b'SDIFFSTORE', destination.encode(), key.encode(), *map(lambda x: x.encode(), other_keys)
		)

	async def sinter(self, key, *other_keys):
		return await self.protocol.send(b'SINTER', key.encode(), *map(lambda x: x.encode(), other_keys))

	async def sinterstore(self, destination, key, *other_keys):
		return await self.protocol.send(
			b'SINTERSTORE', destination.encode(), key.encode(), *map(lambda x: x.encode(), other_keys)
		)

	async def sismember(self, key, member):
		return await self.protocol.send(b'SISMEMBER', key.encode(), member.encode())

	async def smembers(self, key):
		return await self.protocol.send(b'SMEMBERS', key.encode())

	async def smove(self, source, destination, member):
		return await self.protocol.send(b'SMOVE', source.encode(), destination.encode(), member.encode())

	async def spop(self, key):
		return await self.protocol.send(b'SPOP', key.encode())

	async def srandmember(self, key, count=None):
		_ = []
		if isinstance(count, int) and count > 0:
			_.append(to_bytes(count))

		return await self.protocol.send(b'SRANDMEMBER', key.encode(), *_)

	async def srem(self, key, *members):
		return await self.protocol.send(b'SREM', key.encode(), *map(utf8, members))

	async def sunion(self, key, *other_keys):
		return await self.protocol.send(b'SUNION', key.encode(), *map(lambda x: x.encode(), other_keys))

	async def sunionstore(self, destination, key, *other_keys):
		return await self.protocol.send(
			b'SUNIONSTORE', destination.encode(), key.encode(), *map(lambda x: x.encode(), other_keys)
		)

	async def sscan(self):
		pass
