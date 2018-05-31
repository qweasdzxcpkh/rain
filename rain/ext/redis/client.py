import asyncio

from rain.ext.redis.utils import to_bytes
from rain.ext.redis.base import RedisProtocol
from rain.ext.redis.cs4key import KeyMix
from rain.ext.redis.cs4string import StringMix
from rain.ext.redis.cs4hash import HashMix
from rain.ext.redis.cs4list import ListMix


class Redis(KeyMix, StringMix, HashMix, ListMix):
	def __init__(self, port=6379, db=0):
		self.port = port
		self.loop = asyncio.get_event_loop()
		self.db = db

		self.protocol = None  # type: RedisProtocol
		self.transport = None

	def start(self):
		self.transport, self.protocol = self.loop.run_until_complete(
			self.loop.create_connection(
				RedisProtocol,
				host='localhost',
				port=self.port
			)
		)

		self.loop.run_until_complete(self.select(self.db))

	async def select(self, db):
		return await self.protocol.send(b'SELECT', to_bytes(db))


if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.set_debug(True)

	r = Redis(db=2)
	r.start()

	print(loop.run_until_complete(r.mget('name', 'prince')))

	loop.run_forever()
