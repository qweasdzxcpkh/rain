from rain.ext.redis.base import BaseMix


class KeyMix(BaseMix):
	async def delete(self, *keys) -> int:
		return await self._send(b'DEL', *keys)

	async def exists(self, key) -> bool:
		return await self._send(b'EXISTS', key) == 1

	async def expire(self, key, seconds) -> int:
		return await self._send(b'EXPIRE', key, seconds)

	async def pexpire(self, key, milliseconds):
		return await self._send(b'PEXPIRE', key, milliseconds)

	async def ttl(self, key):
		return await self._send(b'TTL', key)

	async def pttl(self, key):
		return await self._send(b'PTTL', key)

	async def keys(self, pattern):
		return await self._send(b'KEYS', pattern)

	async def persist(self, key):
		return await self._send(b'PERSIST', key)

	async def randomkey(self):
		return await self._send(b'RANDOMKEY')

	async def rename(self, key, new_key):
		return await self._send(b'RENAME', key, new_key)

	async def sort(self, key, desc=False, alpha=False, offset=0, count=0, by=None):
		# todo ext keys

		_ = []
		if desc:
			_.append(b'DESC')

		if alpha:
			_.append(b'ALPHA')

		if offset > 0 or count > 0:
			_.append('LIMIT {} {}'.format(offset, count).encode('ascii'))

		if by:
			_.append('BY {}'.format(by))

		return await self._send(b'SORT', key, *_)

	async def type(self, key):
		return await self._send(b'TYPE', key)

	async def scan(self, cursor=0, pattern=None, count=10):
		_ = []
		if pattern:
			_ += [b'MATCH', pattern]
		if count != 10:
			_ += [b'COUNT', count]

		return await self._send(b'SCAN', cursor, *_)
