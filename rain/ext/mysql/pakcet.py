import os
from io import BytesIO
import struct

from rain.ext.mysql.constants import FIELD_TYPE
from rain.ext.mysql.converters import TO_STRING

from rain.ext.mysql.error import MysqlError

NULL_COLUMN = 251
UNSIGNED_CHAR_COLUMN = 251
UNSIGNED_SHORT_COLUMN = 252
UNSIGNED_INT24_COLUMN = 253
UNSIGNED_INT64_COLUMN = 254


def _read_length(c):
	if c < UNSIGNED_CHAR_COLUMN:
		return c
	elif c == UNSIGNED_SHORT_COLUMN:
		return -2
	elif c == UNSIGNED_INT24_COLUMN:
		return -3
	elif c == UNSIGNED_INT64_COLUMN:
		return -8


class MysqlPacket(BytesIO):
	def __repr__(self):
		return '<{} {}>'.format(self.__class__.__name__, self.packet_number)

	@classmethod
	def make_packet(cls, data, expect_length, packet_number):
		length = len(data)
		head = data[0:1]

		if head == b'\xff':
			pass

		p_cls = MysqlPacket

		if 1 <= ord(head) <= 250:
			p_cls = MysqlResultPacket
		elif head == b'\xfb':
			p_cls = MysqlLLPacket
		elif head == b'\xff':
			p_cls = MysqlErrorPacket

		return p_cls(data, expect_length, length, packet_number, head)

	def __init__(self, init_bytes, expect_length, length, packet_number, head):
		super().__init__(init_bytes)
		self.expect_length = expect_length
		self.length = length
		self.packet_number = packet_number
		self.head = head

	def __await__(self):
		return

	def append(self, bs):
		self.length += len(bs)
		super().write(self.getvalue() + bs)
		self.seek(0)

	def read_until(self, sign=b'\0'):
		_ = self.getvalue()
		c = self.tell()

		ind = _.find(sign, c)
		if ind < 0:
			return None

		result = _[c: ind]
		self.seek(ind)

		return result

	def read_uint8(self, safe=False):
		if safe:
			_ = self.read(1)
			if not _:
				return None
			return ord(_)
		return ord(self.read(1))

	def read_uint16(self):
		return struct.unpack('<H', self.read(2))[0]

	def read_uint24(self):
		return struct.unpack('<HB', self.read(3))[0]

	def read_uint32(self):
		return struct.unpack('<I', self.read(4))[0]

	def read_uint64(self):
		return struct.unpack('<Q', self.read(8))[0]

	def read_string(self):
		return self.read_until()

	def read_length_encoded_integer(self, safe=False):
		c = self.read_uint8(safe=safe)

		if c == NULL_COLUMN or c is None:
			return None
		if c < UNSIGNED_CHAR_COLUMN:
			return c
		elif c == UNSIGNED_SHORT_COLUMN:
			return self.read_uint16()
		elif c == UNSIGNED_INT24_COLUMN:
			return self.read_uint24()
		elif c == UNSIGNED_INT64_COLUMN:
			return self.read_uint64()

	def read_length_coded_string(self, safe=False):
		length = self.read_length_encoded_integer(safe=safe)
		if length is None:
			return None
		return self.read(length)

	def is_ok(self):
		return self.head == b'\0' and self.length >= 7

	def is_eof(self):
		return self.head == b'\xfe' and self.length < 9

	def is_auth_switch_request(self):
		return self.head == b'\xfe'

	def is_load_local_packet(self):
		return self.head == b'\xfb'

	def error_msg(self):
		pass

	def read_field(self, coding):
		pass

	def read_column(self, fields, converters, row_class):
		pass

	def send_file(self, conn):
		pass


TEXT_TYPES = {
	FIELD_TYPE.BIT,
	FIELD_TYPE.BLOB,
	FIELD_TYPE.LONG_BLOB,
	FIELD_TYPE.MEDIUM_BLOB,
	FIELD_TYPE.STRING,
	FIELD_TYPE.TINY_BLOB,
	FIELD_TYPE.VAR_STRING,
	FIELD_TYPE.VARCHAR,
	FIELD_TYPE.GEOMETRY,
	FIELD_TYPE.JSON
}


class Field(object):
	__slots__ = (
		'catalog', 'db', 'table_name',
		'name', 'org_table', 'org_name',
		'charsetnr', 'length', 'flags',
		'type_code', 'scale', 'coding'
	)

	def __init__(self):
		self.catalog = None
		self.db = None
		self.table_name = None
		self.org_table = None
		self.name = None
		self.org_name = None

		self.charsetnr = None
		self.length = None
		self.type_code = None
		self.flags = None
		self.scale = None

		self.coding = None

	def __repr__(self):
		return '<Field {}.{}.{}>'.format(self.db, self.table_name, self.name)

	def decode(self, raw, converters: dict):
		type_code = self.type_code
		converter = converters.get(type_code)

		if converter is None:
			return raw

		if converter == TO_STRING:
			return raw.decode(self.coding, 'ignore')

		return converter(raw)


class MysqlResultPacket(MysqlPacket):
	def is_load_local_packet(self):
		return False

	def read_field(self, coding):
		field = Field()
		field.coding = coding

		field.catalog = self.read_length_coded_string()
		field.db = self.read_length_coded_string().decode(coding)
		field.table_name = self.read_length_coded_string().decode(coding)
		field.org_table = self.read_length_coded_string()
		field.name = self.read_length_coded_string().decode(coding)
		field.org_name = self.read_length_coded_string()

		_ = struct.unpack('<xHIBHBxx', self.read(13))
		field.charsetnr, field.length, field.type_code, field.flags, field.scale = _

		return field

	def read_row(self, fields, converters, row_class):
		row = row_class()
		end = self.length

		row_num = 0
		while self.tell() != end:
			_ = self.read_length_coded_string()
			field = fields[row_num]

			if _ is None:
				row.append(field, _)
			else:
				row.append(field, field.decode(_, converters))

			row_num += 1

		return row


class MysqlErrorPacket(MysqlPacket):
	def __init__(self, *args):
		super().__init__(*args)

		raise MysqlError(*self.error_msg())

	def error_msg(self):
		self.read(1)
		return self.read_uint16(), self.read()


class MysqlLLPacket(MysqlPacket):
	def __init__(self, *args):
		super().__init__(*args)
		self.read(1)
		self.filename = self.read().decode()

	def is_load_local_packet(self):
		return True

	async def send_file(self, conn):
		if not os.path.exists(self.filename):
			raise MysqlError(1017, "Can't find file '{0}'".format(self.filename))

		with open(self.filename, 'rb') as f:
			data = f.read()

		return await conn.send_packet(data)
