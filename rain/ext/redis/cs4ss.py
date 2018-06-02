from rain.ext.redis.base import BaseMix
from rain.ext.redis.utils import utf8, to_bytes


class SortedSetMix(BaseMix):
	async def zadd(self, key, *sms):
		_ = len(sms)
		assert _ > 0 and _ % 2 == 0

		return await self.protocol.send(
			b'ZADD', key.encode(), *map(
				lambda x: x[1].encoed() if x[0] % 2 == 0 else to_bytes(x[1]),
				enumerate(sms)
			)
		)
