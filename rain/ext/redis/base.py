import asyncio

from rain.ext.redis.utils import parse_packet, escape


class RedisProtocol(asyncio.Protocol):
	def __init__(self):
		self.transport: asyncio.Transport = None
		self.future: asyncio.Future = None

	def connection_made(self, transport):
		self.transport = transport

	def data_received(self, data):
		self.future.set_result(parse_packet(data))

	async def send(self, *args):
		self.transport.write(b' '.join(map(escape, args)))
		self.transport.write(b'\r\n')

		self.future = asyncio.Future()

		return await self.future


class BaseMix(object):
	protocol: RedisProtocol = None


class RedisError(Exception):
	pass
