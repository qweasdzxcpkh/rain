import asyncio
import random


class _ConnCtx(object):
	__slots__ = ('conn', 'pool')

	def __init__(self, pool):
		self.conn = None
		self.pool: Pool = pool

	async def __aenter__(self):
		self.conn = await self.pool.acquire()
		return self.conn

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		self.pool.release(self.conn)


class _TransactionCtx(_ConnCtx):
	__slots__ = ('conn', 'pool', '_rollback')

	def __init__(self, pool, rollback_on_error=True):
		super().__init__(pool)
		self._rollback = rollback_on_error

	async def __aenter__(self):
		self.conn = await self.pool.acquire()
		return self.conn

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		try:
			if exc_type and self._rollback:
				await self.conn.rollback()
			else:
				await self.conn.commit()
		finally:
			self.pool.release(self.conn)


class Pool(object):
	def __init__(self, *conns):
		self.conns = set(conns)
		self.locks_conns = set()
		self.size = len(self.conns)

		self.futures = []

	def conn_ctx(self):
		return _ConnCtx(self)

	def tran_ctx(self, rollback_on_error=True):
		return _TransactionCtx(self, rollback_on_error=rollback_on_error)

	async def acquire(self):
		if len(self.locks_conns) == self.size:
			future = asyncio.Future()
			self.futures.append(future)
			return await future

		conn = random.choice(list(self.conns - self.locks_conns))
		self.conns.remove(conn)
		self.locks_conns.add(conn)
		return conn

	def release(self, conn):
		if self.futures:
			f: asyncio.Future = self.futures.pop()
			f.set_result(conn)
		else:
			self.locks_conns.remove(conn)
			self.conns.add(conn)
