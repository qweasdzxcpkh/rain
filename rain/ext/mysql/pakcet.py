from io import BytesIO
import struct

NULL_COLUMN = 251
UNSIGNED_CHAR_COLUMN = 251
UNSIGNED_SHORT_COLUMN = 252
UNSIGNED_INT24_COLUMN = 253
UNSIGNED_INT64_COLUMN = 254


class MysqlPacket(BytesIO):
	def __init__(self, init_bytes):
		super().__init__(init_bytes)
		self.length = len(init_bytes)

		self.btrl, self.btrh, self.packet_number = struct.unpack('<HBB', self.read(4))

	def current_head(self):
		_ = self.read(1)
		self.seek(self.tell() - 1)
		return _

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

	def is_ok(self):
		return self.current_head() == b'\0' and self.length >= 7

	def is_eof(self):
		return self.current_head() == b'\0' and self.length < 9

	def is_auth_switch_request(self):
		return self.current_head() == b'\xfe'

	def is_resultset(self):
		return 1 <= ord(self.current_head()) <= 250

	def is_load_local(self):
		return self.current_head() == b'\xfb'

	def is_error(self):
		return self.current_head() == b'\xff'
