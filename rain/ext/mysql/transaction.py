class Transaction(object):
	__slots__ = ('client', 'conn', 'pool', '_execute_count')

	def __init__(self, client):
		self.client = client
		self.conn = None
		self.pool = client.pool

		self._execute_count = 0

	async def __aenter__(self):
		self.conn = (await self.client.pool.acquire()).conn
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		try:
			if exc_type:
				await self.conn.rollback()
			elif self._execute_count > 0:
				await self.conn.commit()
		finally:
			self.pool.release(self.conn)

	async def execute(self, sql):
		packet = await self.conn.execute(sql)
		self._execute_count += 1
		return packet

	async def query(self, sql):
		return await self.conn.query(sql)
