import asyncio

from rain.ext.mysql.pakcet import MysqlPacket


class FutureDict(dict):
	def __init__(self):
		super().__init__()
		self.fs = {}
		self.locks = {}

	def __setitem__(self, key, value, lock=False):
		if lock:
			self.locks[key] = asyncio.Future()

		if key in self.fs:
			self.fs.pop(key).set_result(value)
			return

		super().__setitem__(key, value)

	async def pop(self, k):
		lock_future = self.locks.get(k)
		if lock_future:
			await lock_future

		if k in self:
			return super().pop(k)
		else:
			f = asyncio.Future()
			self.fs[k] = f
			return await f

	def lock_set(self, k, v):
		self.__setitem__(k, v, lock=True)

	def release_get(self, k):
		lock_future = self.locks.get(k)
		if lock_future:
			lock_future.set_result(None)

		return self.get(k)


class MysqlFuture(asyncio.Future):
	def __init__(self, seq_id):
		super().__init__()
		self.bt = asyncio.get_event_loop().time()
		self.et = None

		self.seq_id = seq_id

	def set_result(self, packet: MysqlPacket):
		super().set_result(packet)
		self.et = asyncio.get_event_loop().time()


async def set_packet(pop, packet):
	future: asyncio.Future = await pop
	future.set_result(packet)


class MysqlProtocol(asyncio.Protocol):
	def __init__(self, client):
		self.client = client
		self.transport: asyncio.Transport = None

		self.futures = FutureDict()

	def connection_made(self, transport):
		self.transport = transport
		self.futures.lock_set(0, MysqlFuture(0))

	def data_received(self, data):
		packet = MysqlPacket.make_packet(data)
		pop = self.futures.pop(packet.packet_number)
		asyncio.get_event_loop().create_task(set_packet(pop, packet))

	async def send(self, data, seq_id):
		self.transport.write(data)
		future = MysqlFuture(seq_id)
		self.futures[seq_id + 1] = future
		return await future
