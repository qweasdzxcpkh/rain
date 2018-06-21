import asyncio
import random
import time
from inspect import isawaitable

from rain.ext.mysql.connection import Connection


class _ConnCtx(object):
	__slots__ = ('conn', 'pool')

	def __init__(self, pool):
		self.conn = None
		self.pool: Pool = pool

	async def __aenter__(self) -> Connection:
		self.conn = await self.pool.acquire()
		return self.conn

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		await self.pool.release(self.conn)


class _TransactionCtx(_ConnCtx):
	__slots__ = ('conn', 'pool', '_rollback')

	def __init__(self, pool, rollback_on_error=True):
		super().__init__(pool)
		self._rollback = rollback_on_error

	async def __aenter__(self) -> Connection:
		self.conn = await self.pool.acquire()
		return self.conn

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		try:
			if exc_type and self._rollback:
				await self.conn.rollback()
			else:
				await self.conn.commit()
		finally:
			await self.pool.release(self.conn)


class Pool(object):
	def __init__(self, size, new_connection_func, recycle):
		self.conns = set()
		self.locks_conns = set()
		self.size = size
		self.recycle = recycle - 300

		self.futures = []

		self.new_connection_func = new_connection_func

	def conn_ctx(self):
		return _ConnCtx(self)

	def tran_ctx(self, rollback_on_error=True):
		return _TransactionCtx(self, rollback_on_error=rollback_on_error)

	async def _flush_conn(self, conn):
		if time.time() - conn.init_time > self.recycle:
			self.locks_conns.remove(conn)
			conn = await self.new_connection_func()
			self.locks_conns.add(conn)

		return conn

	async def acquire(self):
		if len(self.locks_conns) + len(self.conns) != self.size:
			_ = self.new_connection_func()
			if isawaitable(_):
				_ = await _

			self.conns.add(_)

		if len(self.locks_conns) == self.size:
			future = asyncio.Future()
			self.futures.append(future)
			return await future

		conn = random.choice(list(self.conns - self.locks_conns))
		self.conns.remove(conn)
		self.locks_conns.add(conn)
		return await self._flush_conn(conn)

	async def release(self, conn):
		if self.futures:
			f: asyncio.Future = self.futures.pop()
			f.set_result(await self._flush_conn(conn))
		else:
			self.locks_conns.remove(conn)
			self.conns.add(conn)
