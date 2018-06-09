import io
from asyncio.streams import StreamReader, StreamWriter
import struct
import hashlib
from functools import partial

from rain.ext.mysql.charset import charset_by_id, charset_by_name
from rain.ext.mysql.constants import CLIENT, COMMAND, ER
from rain.ext.mysql.utils import int2byte, byte2int

from rain.ext.mysql.error import MysqlError
from rain.ext.mysql.pakcet import MysqlPacket

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


SCRAMBLE_LENGTH_323 = 8


def _hash_password_323(password):
	nr = 1345345333
	add = 7
	nr2 = 0x12345671

	# x in py3 is numbers, p27 is chars
	for c in [byte2int(x) for x in password if x not in (' ', '\t', 32, 9)]:
		nr ^= (((nr & 63) + add) * c) + (nr << 8) & 0xFFFFFFFF
		nr2 = (nr2 + ((nr2 << 8) ^ nr)) & 0xFFFFFFFF
		add = (add + c) & 0xFFFFFFFF

	r1 = nr & ((1 << 31) - 1)  # kill sign bits
	r2 = nr2 & ((1 << 31) - 1)
	return struct.pack(">LL", r1, r2)


# noinspection PyPep8Naming
class RandStruct_323(object):
	def __init__(self, seed1, seed2):
		self.max_value = 0x3FFFFFFF
		self.seed1 = seed1 % self.max_value
		self.seed2 = seed2 % self.max_value

	def my_rnd(self):
		self.seed1 = (self.seed1 * 3 + self.seed2) % self.max_value
		self.seed2 = (self.seed1 + self.seed2 + 33) % self.max_value
		return float(self.seed1) / float(self.max_value)


def _scramble_323(password, message):
	hash_pass = _hash_password_323(password)
	hash_message = _hash_password_323(message[:SCRAMBLE_LENGTH_323])
	hash_pass_n = struct.unpack(">LL", hash_pass)
	hash_message_n = struct.unpack(">LL", hash_message)

	rand_st = RandStruct_323(
		hash_pass_n[0] ^ hash_message_n[0],
		hash_pass_n[1] ^ hash_message_n[1]
	)

	outbuf = io.BytesIO()
	for _ in range(min(SCRAMBLE_LENGTH_323, len(message))):
		outbuf.write(int2byte(int(rand_st.my_rnd() * 31) + 64))
	extra = int2byte(int(rand_st.my_rnd() * 31))
	out = outbuf.getvalue()
	outbuf = io.BytesIO()
	for c in out:
		outbuf.write(int2byte(byte2int(c) ^ byte2int(extra)))
	return outbuf.getvalue()


MAX_PACKET_LEN = 2 ** 24 - 1


# noinspection SqlDialectInspection,SqlNoDataSourceInspection
class Connection(object):
	def __init__(self, client, reader, writer):
		self.client = client
		self.loop = client.loop
		self.client_flag = client.client_flag
		self.encoding = client.encoding
		self.charset = client.charset

		self.user = client.user.encode(self.encoding)
		self.password = client.password.encode('latin1')
		self.db = client.db.encode(self.encoding)

		self.reader: StreamReader = reader
		self.writer: StreamWriter = writer

		self.protocol_version = None
		self.server_version = None
		self.server_thread_id = None
		self.salt = None
		self.server_capabilities = None
		self.server_lang = None
		self.server_charset = None
		self.server_status = None
		self.server_auth_plugin_name = None

		self._next_seq_id = 0

	def next_seq_id(self):
		_ = (self._next_seq_id + 1) % 256
		self._next_seq_id = _
		return _

	async def read_packet(self, seq_id):
		btrl, btrh, packet_number = struct.unpack('<HBB', await self.reader.read(4))
		bytes_to_read = btrl + (btrh << 16)
		packet = MysqlPacket.make_packet(
			await self.reader.read(bytes_to_read),
			bytes_to_read,
			packet_number
		)

		while True:
			need_length = packet.expect_length - packet.length
			if need_length == 0:
				break
			packet.append(await self.reader.read(need_length))

		if packet_number != seq_id:
			raise MysqlError(1, 'Connection Lost')

		return packet

	async def send(self, data, seq_id):
		self.writer.write(data)
		return await self.read_packet(seq_id=seq_id + 1)

	async def send_packet(self, payload):
		self.next_seq_id()
		data = pack_int24(len(payload)) + int2byte(self._next_seq_id) + payload
		return await self.send(data, self._next_seq_id)

	async def get_server_info(self):
		info: MysqlPacket = await self.read_packet(0)

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
		self.user = self.user

		data = struct.pack('<iIB23s', self.client_flag, 1, charset_id, b'')
		data += (self.user + b'\0')

		auth = b''
		if self.server_auth_plugin_name in {None, 'mysql_native_password'}:
			auth = _scramble(self.password, self.salt)

		if self.server_capabilities & CLIENT.PLUGIN_AUTH_LENENC_CLIENT_DATA:
			data += lenenc_int(len(auth)) + auth
		elif self.server_capabilities & CLIENT.SECURE_CONNECTION:
			data += struct.pack('B', len(auth)) + auth
		else:
			data += auth + b'\0'

		if self.db and self.server_capabilities & CLIENT.CONNECT_WITH_DB:
			data += (self.db + b'\0')

		if self.server_capabilities & CLIENT.PLUGIN_AUTH:
			name = self.server_auth_plugin_name
			name = name.encode('ascii')
			data += (name + b'\0')

		resp: MysqlPacket = await self.send_packet(data)

		if not resp.is_auth_switch_request():
			return

		resp.read(2)
		plugin_name = resp.read_string()

		if self.server_capabilities & CLIENT.PLUGIN_AUTH and plugin_name is not None:
			auth_packet: MysqlPacket = await self._process_auth(plugin_name, resp)
		else:
			data = _scramble_323(self.password.encode('latin1'), self.salt) + b'\0'
			auth_packet: MysqlPacket = await self.send_packet(data)

		error = auth_packet.error_msg()
		if error:
			raise MysqlError(2, 'Auth Error {} {}'.format(*error))

	async def _process_auth(self, plugin_name, auth_packet):
		data = False

		if plugin_name == b'mysql_native_password':
			data = _scramble(self.password.encode('latin1'), auth_packet.read())
		elif plugin_name == b'mysql_old_password':
			data = _scramble_323(self.password.encode('latin1'), auth_packet.read_all()) + b'\0'
		elif plugin_name == b'mysql_clear_password':
			data = self.password.encode('latin1') + b'\0'
		elif plugin_name == b'dialog':
			auth_packet.read(2)
			prompt = auth_packet.read()
			if prompt == b"Password: ":
				return await self.send_packet(self.password.encode('latin1') + b'\0')
			else:
				raise MysqlError(2059, 'Auth Plugin: "{}" is not supported'.format(plugin_name))

		if not data:
			raise MysqlError(2059, 'Auth Plugin: "{}" is not supported'.format(plugin_name))

		return await self.send_packet(data)

	async def init(self):
		await self.get_server_info()
		await self.do_auth()

	async def execute_command(self, command, sql):
		if isinstance(sql, str):
			sql = sql.encode(self.encoding)

		packet_size = len(sql) + 1
		if packet_size > MAX_PACKET_LEN:
			raise MysqlError(3, "Your sql is too too too too large")

		prelude = struct.pack('<iB', packet_size, command)
		self._next_seq_id = 0
		self.next_seq_id()

		packet: MysqlPacket = await self.send(prelude + sql, 0)
		error = packet.error_msg()
		if error:
			raise MysqlError(*error)

		if packet.is_load_local_packet():
			return await packet.send_file(self)

		return packet

	async def ping(self):
		begin = self.loop.time()
		packet = await self.execute_command(COMMAND.COM_PING, b'')

		return packet.is_ok() and self.loop.time() - begin

	async def kill(self, thread_id):
		return (
			await self.execute_command(COMMAND.COM_PROCESS_KILL, struct.pack('<I', thread_id))
		).is_ok()

	async def use(self, db):
		return (await self.execute_command(COMMAND.COM_INIT_DB, db)).is_ok()

	async def create_db(self, db):
		try:
			packet = await self.execute_command(COMMAND.COM_QUERY, 'CREATE DATABASE {}'.format(db))
		except MysqlError as e:
			if e.error_no == ER.DB_CREATE_EXISTS:
				return True
			raise

		return packet.is_ok()

	async def create_table(self, sql):
		try:
			packet = await self.execute_command(COMMAND.COM_QUERY, sql)
		except MysqlError as e:
			if e.error_no == ER.TABLE_EXISTS_ERROR:
				return True

			raise

		return packet.is_ok()
