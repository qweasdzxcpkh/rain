import asyncio
from asyncio import StreamWriter, StreamReader

from rain.ext.redis.packet import escape, parse_packet

from rain.ext.redis.cs4geo import GEOMix
from rain.ext.redis.cs4hash import HashMix
from rain.ext.redis.cs4hyperloglog import HyperLogLogMix
from rain.ext.redis.cs4key import KeyMix
from rain.ext.redis.cs4list import ListMix
from rain.ext.redis.cs4pubsub import PubAndSubMix
from rain.ext.redis.cs4script import ScriptMix
from rain.ext.redis.cs4set import SetMix
from rain.ext.redis.cs4sortedset import SortedSetMix
from rain.ext.redis.cs4string import StringMix
from rain.ext.redis.cs4transaction import TransactionMix


class Redis(
	GEOMix, HashMix, HyperLogLogMix,
	KeyMix, ListMix, PubAndSubMix,
	ScriptMix, SetMix, SortedSetMix,
	StringMix, TransactionMix
):
	def __init__(self, host='localhost', port=6379, db=0, password=None):
		self.host = host
		self.port = port
		self.loop = asyncio.get_event_loop()
		self.db = db
		self._password = password

		self.reader: StreamReader = None
		self.writer: StreamWriter = None

		self._started = False
		self._future = None

	async def start(self):
		self.reader, self.writer = await asyncio.open_connection(host=self.host, port=self.port, loop=self.loop)
		await self.select(self.db)
		if self._password:
			await self.auth(self._password)

		self._started = True

	async def _read_packet(self):
		return await parse_packet(self.reader)

	async def _send(self, *args):
		self.writer.write(b' '.join(map(escape, args)))
		self.writer.write(b'\r\n')

		return await self._read_packet()

	async def select(self, db):
		if self._started:
			raise RuntimeError('RedisClient is running')

		await self._send(b'SELECT', db)

	async def auth(self, password):
		await self._send(b'AUTH', password)

	async def echo(self, message):
		return await self._send(b'ECHO', message)

	async def ping(self, cost_time=False):
		if not cost_time:
			return await self._send(b'PING')

		_ = self.loop.time()
		await self._send(b'PING')
		return self.loop.time() - _

	async def quit(self):
		return await self._send(b'QUIT')
