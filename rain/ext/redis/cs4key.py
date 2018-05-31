from rain.ext.redis.utils import to_bytes
from rain.ext.redis.base import BaseMix


class KeyMix(BaseMix):
	async def delete(self, *keys):
		return await self.protocol.send(b'DEL', *map(lambda x: x.encode(), keys))

	async def exists(self, key):
		return await self.protocol.send(b'EXISTS', key.encode())

	async def expire(self, key, seconds):
		return await self.protocol.send(b'EXPIRE', key.encode(), to_bytes(seconds))

	async def pexpire(self, key, milliseconds):
		return await self.protocol.send(b'PEXPIRE', key.encode(), to_bytes(milliseconds))

	async def ttl(self, key):
		return await self.protocol.send(b'TTL', key.encode())

	async def pttl(self, key):
		return await self.protocol.send(b'PTTL', key.encode())

	async def keys(self, pattern):
		return await self.protocol.send(b'KEYS', pattern.encode())

	async def persist(self, key):
		return await self.protocol.send(b'PERSIST', key.encode())

	async def randomkey(self):
		return await self.protocol.send(b'RANDOMKEY')

	async def rename(self, key, new_key):
		return await self.protocol.send(b'RENAME', key.encode(), new_key.encode())

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
			_.append('BY {}'.format(by).encode())

		return await self.protocol.send(b'SORT', key.encode(), *_)

	async def type(self, key):
		return await self.protocol.send(b'TYPE', key.encode())

	async def scan(self, cursor=0, pattern=None, count=10):
		_ = []
		if pattern:
			_ += [b'MATCH', pattern.encode()]
		if count != 10:
			_ += [b'COUNT', to_bytes(count)]

		return await self.protocol.send(b'SCAN', to_bytes(cursor), *_)
