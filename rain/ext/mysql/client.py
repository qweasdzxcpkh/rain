import asyncio

from rain.ext.mysql.charset import charset_by_name
from rain.ext.mysql.constants import CLIENT, COMMAND

from rain.ext.mysql.connection import Connection
from rain.ext.mysql.converters import mysql_decoders
from rain.ext.mysql.pool import Pool


class Mysql(object):
	def __init__(
			self,
			host='localhost', port=3306,
			pool_class=Pool, pool_size=5,
			user=None, password=None, database=None,
			charset='latin1',
			autocommit=False,
			client_flag=0, local_infile=False,
			converters=None
	):
		self.host = host
		self.port = port
		self.loop = asyncio.get_event_loop()
		self.pool_size = pool_size

		self.db = database
		self.user = user
		self.password = password
		self.charset = charset
		self.encoding = charset_by_name(self.charset).encoding
		self.autocommit = int(bool(autocommit))

		self._local_infile = bool(local_infile)
		if self._local_infile:
			client_flag |= CLIENT.LOCAL_FILES

		client_flag |= CLIENT.CAPABILITIES
		if self.db:
			client_flag |= CLIENT.CONNECT_WITH_DB
		self.client_flag = client_flag

		mysql_decoders.update(converters or {})

		self.converters = mysql_decoders

		_ = []
		for i in range(pool_size):
			_.append(self._make_connection())

		self.pool: Pool = pool_class(*_)

	def _make_connection(self):
		connection = Connection(
			self, *self.loop.run_until_complete(
				asyncio.open_connection(host=self.host, port=self.port)
			)
		)

		self.loop.run_until_complete(connection.init())

		return connection

	def conn_ctx(self):
		return self.pool.conn_ctx()

	def tran_ctx(self, rollback_on_error=True):
		if self.autocommit:
			raise ValueError('CLIENT IS IN AUTO_COMMIT MODE')

		return self.pool.tran_ctx(rollback_on_error=rollback_on_error)

	async def query(self, sql):
		async with self.conn_ctx() as conn:
			return await conn.query(sql)

	async def execute(self, sql):
		async with self.conn_ctx() as conn:
			await conn.execute_command(COMMAND.COM_QUERY, sql)
