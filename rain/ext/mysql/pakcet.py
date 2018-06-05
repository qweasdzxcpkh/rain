from io import BytesIO
import struct

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
	@classmethod
	def make_packet(cls, data):
		length = len(data)
		btrl, btrh, packet_number = struct.unpack('<HBB', data[:4])
		head = data[4:5]

		if head == b'\xff':
			pass

		p_cls = MysqlPacket

		if 1 <= ord(head) <= 250:
			p_cls = MysqlResultPacket
		elif head == b'\xfb':
			p_cls = MysqlLLPacket
		elif head == b'\xff':
			p_cls = MysqlErrorPacket

		return p_cls(data[4:], length, packet_number, head)

	def __init__(self, init_bytes, length, packet_number, head):
		super().__init__(init_bytes)
		self.length = length
		self.packet_number = packet_number
		self.head = head

	def read_until(self, sign=b'\0'):
		_ = self.getvalue()
		c = self.tell()

		ind = _.find(sign, c)
		if ind < 0:
			return None

		result = _[c: ind]
		self.seek(ind)

		return result

	def read_uint8(self):
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

	def read_length_encoded_integer(self):
		c = self.read_uint8()
		if c == NULL_COLUMN:
			return None
		if c < UNSIGNED_CHAR_COLUMN:
			return c
		elif c == UNSIGNED_SHORT_COLUMN:
			return self.read_uint16()
		elif c == UNSIGNED_INT24_COLUMN:
			return self.read_uint24()
		elif c == UNSIGNED_INT64_COLUMN:
			return self.read_uint64()

	def read_length_coded_string(self):
		length = self.read_length_encoded_integer()
		if length is None:
			return None
		return self.read(length)

	def read_struct(self, fmt):
		s = struct.Struct(fmt)
		return s.unpack_from(self.read(s.size))

	def is_ok(self):
		return self.head == b'\0' and self.length >= 7

	def is_eof(self):
		return self.head == b'\0' and self.length < 9

	def is_auth_switch_request(self):
		return self.head == b'\xfe'

	def error_msg(self):
		pass

	def read_columns(self):
		pass


class Field(object):
	def __init__(self, init_bytes):
		print(init_bytes)
		unknown = init_bytes[:3]
		pos = 3
		end = len(init_bytes) - 1

		result = []
		read_length = None
		while len(result) < 6:
			if pos >= end:
				break

			if read_length is None:
				__ = init_bytes[pos: pos + 1]
				_ = _read_length(ord(__))
				pos += 1

				if _ == -2:
					_ = struct.unpack('<H', init_bytes[pos: pos + 2])[0]
					pos + -2
				elif _ == -3:
					_ = struct.unpack('<HB', init_bytes[pos: pos + 3])[0]
					pos += 3
				elif _ == -8:
					_ = struct.unpack('<Q', init_bytes[pos: pos + 8])[0]
					pos += 8

				read_length = _
			else:
				result.append(init_bytes[pos: pos + read_length])
				pos += read_length
				read_length = None

		assert len(result) == 6 and pos < end

		self.catalog, self.db, self.table_name, self.org_table, self.name, self.org_name = result

		s = struct.Struct('<xHIBHBxx')

		self.charsetnr, self.length, self.type_code, self.flag, self.scale = s.unpack_from(
			init_bytes[pos: pos + s.size]
		)


class MysqlResultPacket(MysqlPacket):
	def __init__(self, *args):
		super().__init__(*args)

		self.field_count = 0
		self.fields = None

	def read_columns(self):
		self.field_count = self.read_length_encoded_integer()
		self.fields = self.read_fields()

	def read_fields(self):
		_ = []

		for i in range(self.field_count):
			length = self.read_length_encoded_integer()
			# i do not know why
			_.append(Field(self.read(length + 3)))

		return _


class MysqlErrorPacket(MysqlPacket):
	def error_msg(self):
		self.read(1)
		return self.read_uint16(), self.read().decode()


class MysqlLLPacket(MysqlPacket):
	pass
