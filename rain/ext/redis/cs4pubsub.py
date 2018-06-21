from rain.ext.redis.base import BaseMix


class PubAndSubMix(BaseMix):
	async def psubscribe(self, *patterns):
		return self._send(b'PSUBSCRIBE', *patterns)

	async def publish(self, channel, message):
		return self._send(b'PUBLISH', channel, message)

	async def pubsub_channels(self, pattern=None):
		_ = []
		if pattern:
			_.append(pattern)
		return await self._send(b'PUBSUB', b'CHANNELS', *_)

	async def pubsub_numsub(self, *channels):
		assert channels
		return await self._send(b'PUBSUB', b'NUMSUB', *channels)

	async def pubsub_numpat(self):
		return await self._send(b'PUBSUB', b'NUMPAT')

	async def punsubscribe(self, *patterns):
		assert patterns
		return await self._send(b'PUNSUBSCRIBE', *patterns)

	async def subscribe(self, *channels):
		assert channels
		return await self._send(b'SUBSCRIBE', *channels)

	async def unsubscribe(self, *channels):
		assert channels
		return await self._send(b'UNSUBSCRIBE', *channels)
