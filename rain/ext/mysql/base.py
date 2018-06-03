import asyncio

from rain.ext.mysql.pakcet import MysqlPacket


class MysqlProtocol(asyncio.Protocol):
	def __init__(self):
		self.transport: asyncio.Transport = None
		self.future: asyncio.Future = asyncio.Future()

	def connection_made(self, transport):
		self.transport = transport

	def data_received(self, data):
		self.future.set_result(MysqlPacket(data))

	async def send(self, data):
		self.transport.write(data)
		self.future = asyncio.Future()

		return await self.future


class MysqlError(Exception):
	pass
