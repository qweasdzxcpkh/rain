import asyncio

from rain.ext.redis.base import RedisProtocol
from rain.ext.redis.cs4key import KeyMix
from rain.ext.redis.cs4string import StringMix
from rain.ext.redis.cs4hash import HashMix
from rain.ext.redis.cs4list import ListMix
from rain.ext.redis.cs4set import SetMix


class Redis(KeyMix, StringMix, HashMix, ListMix, SetMix):
	def __init__(self, host='localhost', port=6379, db=0, password=None):
		self.host = host
		self.port = port
		self.loop = asyncio.get_event_loop()
		self.db = db
		self._password = password

		self.protocol = None  # type: RedisProtocol
		self.transport = None

		self._started = False

	def start(self):
		self.transport, self.protocol = self.loop.run_until_complete(
			self.loop.create_connection(
				RedisProtocol,
				host=self.host,
				port=self.port
			)
		)

		self.loop.run_until_complete(self.select(self.db))
		if self._password:
			self.loop.run_until_complete(self.auth(self._password))

		self._started = True

	async def select(self, db):
		if self._started:
			raise RuntimeError('RedisClient is runing')

		await self.protocol.send(b'SELECT', db)

	async def auth(self, password):
		await self.protocol.send(b'AUTH', password)

	async def echo(self, message):
		return await self.protocol.send(b'ECHO', message)

	async def ping(self):
		return await self.protocol.send(b'PING')

	async def quit(self):
		return await self.protocol.send(b'QUIT')
