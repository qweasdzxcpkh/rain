import asyncio
import struct
import hashlib
from functools import partial

from rain.ext.mysql.base import MysqlProtocol, MysqlPacket
from rain.ext.mysql.charset import charset_by_id, charset_by_name
from rain.ext.mysql.constants import CLIENT
from rain.ext.mysql.utils import int2byte

sha_new = partial(hashlib.new, 'sha1')
SCRAMBLE_LENGTH = 20


def _my_crypt(message1, message2):
	length = len(message1)
	result = b''
	for i in range(length):
		x = (struct.unpack('B', message1[i:i + 1])[0] ^ struct.unpack('B', message2[i:i + 1])[0])
		result += struct.pack('B', x)
	return result


def _scramble(password, message):
	if not password:
		return b''
	stage1 = sha_new(password).digest()
	stage2 = sha_new(stage1).digest()
	s = sha_new()
	s.update(message[:SCRAMBLE_LENGTH])
	s.update(stage2)
	result = s.digest()
	return _my_crypt(result, stage1)


def lenenc_int(i):
	if i < 0:
		raise ValueError("Encoding %d is less than 0 - no representation in LengthEncodedInteger" % i)
	elif i < 0xfb:
		return int2byte(i)
	elif i < (1 << 16):
		return b'\xfc' + struct.pack('<H', i)
	elif i < (1 << 24):
		return b'\xfd' + struct.pack('<I', i)[:3]
	elif i < (1 << 64):
		return b'\xfe' + struct.pack('<Q', i)
	else:
		raise ValueError("Encoding %x is larger than %x - no representation in LengthEncodedInteger" % (i, (1 << 64)))


def pack_int24(n):
	return struct.pack('<I', n)[:3]


class Mysql(object):
	def __init__(
			self,
			host='localhost', port=3306,
			user=None, password=None, database=None,
			charset='latin1',
			client_flag=0, local_infile=False
	):
		self.host = host
		self.port = port
		self.loop = asyncio.get_event_loop()

		self.db = database
		self.user = user
		self.password = password
		self.charset = charset
		self.encoding = charset_by_name(self.charset).encoding

		self.protocol = None  # type: MysqlProtocol
		self.transport = None

		self.protocol_version = None
		self.server_version = None
		self.server_thread_id = None
		self.salt = None
		self.server_capabilities = None
		self.server_lang = None
		self.server_charset = None
		self.server_status = None
		self.server_auth_plugin_name = None

		self._local_infile = bool(local_infile)
		if self._local_infile:
			client_flag |= CLIENT.LOCAL_FILES

		client_flag |= CLIENT.CAPABILITIES
		if self.db:
			client_flag |= CLIENT.CONNECT_WITH_DB
		self.client_flag = client_flag

		self._next_seq_id = 0

	def next_seq_id(self):
		self._next_seq_id = (self._next_seq_id + 1) % 256

	def start(self):
		self.transport, self.protocol = self.loop.run_until_complete(
			self.loop.create_connection(
				MysqlProtocol,
				host=self.host,
				port=self.port
			)
		)

		self.loop.run_until_complete(self.get_server_info())
		self.loop.run_until_complete(self.do_auth())

	async def read(self):
		packet = await self.protocol.future
		self.next_seq_id()

		return packet

	async def send(self, payload):
		data = pack_int24(len(payload)) + int2byte(self._next_seq_id) + payload
		self.next_seq_id()
		return await self.protocol.send(data)

	async def get_server_info(self):
		info: MysqlPacket = await self.read()

		self.protocol_version = info.read_uint8()
		self.server_version = info.read_string().decode('latin1')
		info.read(1)

		self.server_thread_id = info.read_uint32()
		self.salt = info.read(8)
		info.read(1)

		self.server_capabilities = info.read_uint16()

		salt_len = None

		if info.length >= info.tell() + 6:
			lang, stat, cap_h, salt_len = struct.unpack('<BHHB', info.read(6))

			self.server_lang = lang
			self.server_status = stat
			try:
				self.server_charset = charset_by_id(lang)
			except KeyError:
				pass

			self.server_capabilities |= cap_h << 16
			salt_len = max(12, salt_len - 9)

		info.read(10)

		if salt_len is not None and info.length >= info.tell() + salt_len:
			self.salt += info.read(salt_len)

		info.read(1)

		if self.server_capabilities & CLIENT.PLUGIN_AUTH and info.length >= info.tell():
			self.server_auth_plugin_name = info.read_string().decode('latin1')

	async def do_auth(self):
		if int(self.server_version.split('.', 1)[0]) >= 5:
			self.client_flag |= CLIENT.MULTI_RESULTS

		charset_id = charset_by_name(self.charset).id
		self.user = self.user.encode(self.encoding)

		data = struct.pack('<iIB23s', self.client_flag, 1, charset_id, b'')
		data += (self.user + b'\0')

		auth = b''
		if self.server_auth_plugin_name in {None, 'mysql_native_password'}:
			auth = _scramble(self.password.encode('latin1'), self.salt)

		if self.server_capabilities & CLIENT.PLUGIN_AUTH_LENENC_CLIENT_DATA:
			data += lenenc_int(len(auth)) + auth
		elif self.server_capabilities & CLIENT.SECURE_CONNECTION:
			data += struct.pack('B', len(auth)) + auth
		else:
			data += auth + b'\0'

		if self.db and self.server_capabilities & CLIENT.CONNECT_WITH_DB:
			self.db = self.db.encode(self.encoding)
			data += (self.db + b'\0')

		if self.server_capabilities & CLIENT.PLUGIN_AUTH:
			name = self.server_auth_plugin_name
			name = name.encode('ascii')
			data += (name + b'\0')

		resp: MysqlPacket = await self.send(data)

		if resp.is_auth_switch_request():
			pass


if __name__ == '__main__':
	loop = asyncio.get_event_loop()

	client = Mysql(host='47.96.1.64', user='root', password='mnbvcxz?123456', database='mysql')

	client.start()

	loop.run_forever()
