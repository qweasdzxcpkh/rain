from rain.ext.redis.base import BaseMix


class SetMix(BaseMix):
	async def sadd(self, key, *members):
		return await self._send(b'SADD', key, *members)

	async def scadd(self, key):
		return await self._send(b'SCADD', key)

	async def sdiff(self, key, *other_keys):
		return await self._send(b'SDIFF', key, *other_keys)

	async def sdiffstore(self, destination, key, *other_keys):
		return await self._send(
			b'SDIFFSTORE', destination, key, *other_keys
		)

	async def sinter(self, key, *other_keys):
		return await self._send(b'SINTER', key, *other_keys)

	async def sinterstore(self, destination, key, *other_keys):
		return await self._send(
			b'SINTERSTORE', destination, key, *other_keys
		)

	async def sismember(self, key, member):
		return await self._send(b'SISMEMBER', key, member)

	async def smembers(self, key):
		return await self._send(b'SMEMBERS', key)

	async def smove(self, source, destination, member):
		return await self._send(b'SMOVE', source, destination, member)

	async def spop(self, key):
		return await self._send(b'SPOP', key)

	async def srandmember(self, key, count=None):
		_ = []
		if isinstance(count, int) and count > 0:
			_.append(count)

		return await self._send(b'SRANDMEMBER', key, *_)

	async def srem(self, key, *members):
		return await self._send(b'SREM', key, *members)

	async def sunion(self, key, *other_keys):
		return await self._send(b'SUNION', key, *other_keys)

	async def sunionstore(self, destination, key, *other_keys):
		return await self._send(
			b'SUNIONSTORE', destination, key, *other_keys
		)

	async def sscan(self):
		pass
