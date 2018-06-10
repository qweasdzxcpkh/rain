import asyncio

from rain.ext.mysql.charset import charset_by_name
from rain.ext.mysql.constants import CLIENT, COMMAND, ER

from rain.ext.mysql.connection import Connection
from rain.ext.mysql.error import MysqlError
from rain.ext.mysql.converters import mysql_decoders


class Row(object):
	def __init__(self):
		pass

	def append(self, field, value):
		pass


class ListRow(Row, list):
	def append(self, field, value):
		list.append(self, value)


_real_none = object()


class DictRow(Row, dict):
	def append(self, field, value):
		self[field.name] = value


class ObjectRow(DictRow):
	def __getattr__(self, item):
		_ = self.get(item, _real_none)
		if _ is _real_none:
			raise AttributeError(item)

		return _

	def __repr__(self):
		return '<{}>'.format(self.__class__.__name__)


class QueryResult(object):
	row_class = ObjectRow

	__slots__ = ('fields_count', 'fields', 'rows', 'field_names')

	def __init__(self):
		self.fields_count = None
		self.fields = None
		self.rows = None

		self.field_names = None


class Mysql(object):
	def __init__(
			self,
			host='localhost', port=3306,
			pool_size=5,
			user=None, password=None, database=None,
			charset='latin1',
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

		self._local_infile = bool(local_infile)
		if self._local_infile:
			client_flag |= CLIENT.LOCAL_FILES

		client_flag |= CLIENT.CAPABILITIES
		if self.db:
			client_flag |= CLIENT.CONNECT_WITH_DB
		self.client_flag = client_flag

		mysql_decoders.update(converters or {})

		self.converters = mysql_decoders

		self.connections = []

	def make_connection(self):
		connection = Connection(
			self, *self.loop.run_until_complete(
				asyncio.open_connection(host=self.host, port=self.port)
			)
		)

		self.loop.run_until_complete(connection.init())

		self.connections.append(connection)

	def choice_connection(self, identify) -> Connection:
		return self.connections[0]

	def start(self):
		for i in range(self.pool_size):
			self.make_connection()

	async def query(self, sql, identify):
		result = QueryResult()
		result.fields = {}
		result.rows = []

		conn = self.choice_connection(identify)
		first_packet = await conn.execute_command(COMMAND.COM_QUERY, sql)

		fields_count = first_packet.read_length_encoded_integer()
		result.fields_count = fields_count
		packet_number = first_packet.packet_number

		row_num = 0
		for i in range(fields_count):
			packet_number += 1
			field = (await conn.read_packet(packet_number)).read_field(self.encoding)

			result.fields[row_num] = field
			row_num += 1

		packet_number += 1
		is_eof = (await conn.read_packet(packet_number)).is_eof()
		if not is_eof:
			raise MysqlError(3, 'Protocol error, expecting EOF')

		result.field_names = tuple(map(lambda x: result.fields[x].name, sorted(result.fields.keys())))

		packet_number += 1

		next_packet = await conn.read_packet(packet_number)

		while True:
			if next_packet.is_eof():
				break

			packet_number += 1
			row = next_packet.read_row(result.fields, self.converters, result.row_class)
			if row:
				result.rows.append(row)

			next_packet = await conn.read_packet(packet_number)

		return result
