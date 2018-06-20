from rain.ext.redis.base import BaseMix


class GEOMix(BaseMix):
	async def geoadd(self, key, *lolam):
		assert lolam and len(lolam) % 3 == 0
		return await self.protocol.send(b'GEOADD', key, *lolam)

	async def geopos(self, key, *members):
		assert members
		return await self.protocol.send(b'GEOPOS', key, *members)

	async def geodist(self, key, m1, m2, unit='m'):
		unit = unit.lower()
		assert unit in {'m', 'km', 'mi', 'ft'}
		return await self.protocol.send(b'GEODIST', key, m1, m2, unit)

	async def georadius(
			self, key, lo, la, radius,
			unit='m', withcoord=False, withdist=False,
			withhash=False, order=None, count=None
	):
		unit = unit.lower()
		assert unit in {'m', 'km', 'mi', 'ft'}

		_ = []
		if withdist:
			_.append(b'WITHDIST')
		if withcoord:
			_.append(b'WITHCOORD')
		if withhash:
			_.append(b'WITHHASH')

		if order is not None:
			order = order.upper()
			assert order in {'ASC', 'DESC'}
			_.append('ORDER ' + order)

		if count is not None:
			_.append('COUNT {}'.format(count))

		return self.protocol.send(b'GEORADIUS', key, lo, la, radius, unit, *_)

	async def georadiusbymember(
			self, key, member, radius,
			unit='m', withcoord=False, withdist=False,
			withhash=False, order=None, count=None
	):
		unit = unit.lower()
		assert unit in {'m', 'km', 'mi', 'ft'}

		_ = []
		if withdist:
			_.append(b'WITHDIST')
		if withcoord:
			_.append(b'WITHCOORD')
		if withhash:
			_.append(b'WITHHASH')

		if order is not None:
			order = order.upper()
			assert order in {'ASC', 'DESC'}
			_.append('ORDER ' + order)

		if count is not None:
			_.append('COUNT {}'.format(count))

		return self.protocol.send(b'GEORADIUS', key, member, radius, unit, *_)

	async def geohash(self, key, *members):
		assert members
		return self.protocol.send(b'GEOHASH', key, *members)
