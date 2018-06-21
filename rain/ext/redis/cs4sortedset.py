from rain.ext.redis.base import BaseMix


class SortedSetMix(BaseMix):
	ZSCORE_MAX = '+inf'
	ZSCORE_MIN = '-inf'
	ZLEX_MAX = '+'
	ZLEX_MIN = '-'

	async def zadd(self, key, *sms):
		_ = len(sms)
		assert _ > 0 and _ % 2 == 0

		return await self._send(b'ZADD', key, *sms)

	async def zcard(self, key):
		return await self._send(b'ZCARD', key)

	async def zcount(self, key, min_v, max_v):
		return await self._send(b'ZCOUNT', key, min_v, max_v)

	async def zincrby(self, key, increment, member):
		return await self._send(b'ZINCRBY', key, increment, member)

	async def zrange(self, key, start, stop, withscores=False):
		_ = []
		if withscores:
			_.append(b'WITHSCORES')

		return await self._send(b'ZRANGE', key, start, stop, *_)

	async def zrangebyscore(self, key, min_v, max_v, withscores=False, offset=None, limit=None):
		_ = []

		if withscores:
			_.append(b'WITHSCORES')

		if isinstance(offset, int) and isinstance(limit, int):
			_.append('LIMIT {} {}'.format(offset, limit))

		return await self._send(b'ZRANGEBYSCORE', key, min_v, max_v, *_)

	async def zrank(self, key, member):
		return await self._send('ZRANK', key, member)

	async def zrem(self, key, *members):
		assert members
		return await self._send(b'ZREM', key, *members)

	async def zremrangebyrank(self, key, start, stop):
		return await self._send(b'ZREMRANGEBYRANK', key, start, stop)

	async def zremrangebyscore(self, key, min_v, max_v):
		return await self._send(b'ZREMRANGEBYSCORE', key, min_v, max_v)

	async def zrevrange(self, start, stop, withscores=False):
		_ = []
		if withscores:
			_.append(b'WITHSCORES')

		return await self._send(b'ZREVRANGE', start, stop, *_)

	async def zrevrangebyscore(self, key, min_v, max_v, withscores=False, offset=None, limit=None):
		_ = []

		if withscores:
			_.append(b'WITHSCORES')

		if isinstance(offset, int) and isinstance(limit, int):
			_.append('LIMIT {} {}'.format(offset, limit))

		return await self._send(b'ZREVRANGEBYSCORE', key, min_v, max_v, *_)

	async def zrevrank(self, key, member):
		return await self._send(b'ZREVRANK', key, member)

	async def zscore(self, key, member):
		return await self._send(b'ZSCORE', key, member)

	async def zunionstore(self, destination, numberkeys, *keys, weights=None, aggregate=None):
		assert len(keys) == numberkeys

		_ = [destination, numberkeys, *keys]

		if weights:
			assert len(weights) == numberkeys
			_ += weights

		if aggregate:
			aggregate = aggregate.upper()
			assert aggregate in {'SUM', 'MIN', "MAX"}
			_.append('AGGREGATE ' + aggregate)

		return await self._send(b'ZUNIONSTORE', *_)

	async def zinterstore(self, destination, numberkeys, *keys, weights=None, aggregate=None):
		assert len(keys) == numberkeys

		_ = [destination, numberkeys, *keys]

		if weights:
			assert len(weights) == numberkeys
			_ += weights

		if aggregate:
			aggregate = aggregate.upper()
			assert aggregate in {'SUM', 'MIN', "MAX"}
			_.append('AGGREGATE ' + aggregate)

		return await self._send(b'ZINTERSTORE', *_)

	async def zscan(self):
		pass

	async def zrangebylex(self, key, min_v, max_v, offset=None, limit=None):
		_ = []

		if isinstance(offset, int) and isinstance(limit, int):
			_.append('LIMIT {} {}'.format(offset, limit))

		return await self._send(b'ZRANGEBYLEX', key, min_v, max_v, *_)

	async def zlexcount(self, key, min_v, max_v):
		return self._send(b'ZLEXCOUNT', key, min_v, max_v)

	async def zremrangebylex(self, key, min_v, max_v):
		return self._send(b'ZREMRANGEBYLEX', key, min_v, max_v)
