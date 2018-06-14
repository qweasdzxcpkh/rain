import asyncio
import random


class _ConnCtx(object):
	__slots__ = ('conn', 'pool')

	def __init__(self, pool, conn):
		self.conn = conn
		self.pool: Pool = pool

	def __enter__(self):
		return self.conn

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.pool.release(self.conn)


class Pool(object):
	def __init__(self, *conns):
		self.conns = set(conns)
		self.locks_conns = set()
		self.size = len(self.conns)

		self.futures = []

	async def acquire(self):
		if len(self.locks_conns) == self.size:
			future = asyncio.Future()
			self.futures.append(future)
			return await future

		conn = random.choice(list(self.conns - self.locks_conns))
		self.locks_conns.add(conn)
		return _ConnCtx(self, conn)

	def release(self, conn):
		if self.futures:
			f: asyncio.Future = self.futures.pop()
			f.set_result(_ConnCtx(self, conn))
		else:
			self.locks_conns.remove(conn)
			self.conns.add(conn)
