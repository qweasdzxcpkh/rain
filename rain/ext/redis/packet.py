from asyncio import StreamReader

from rain.utils.escape import escape_string

from rain.ext.redis.error import RedisPacketError, RedisError

REDIS_SIMPLE = b'+'
REDIS_ERROR = b'-'
REDIS_INTEGERS = b':'
REDIS_BILK = b'$'
REDIS_ARRAY = b'*'


def escape(s):
	if isinstance(s, bytes):
		return s

	return escape_string(str(s)).encode()


async def _parse_simple(reader: StreamReader):
	return (await reader.readline()).strip().decode('latin1')


async def _parse_error(reader: StreamReader):
	_ = (await reader.readline()).decode('utf8')
	raise RedisError(_)


async def _parse_integers(reader: StreamReader):
	return int((await reader.readline()).strip())


async def _parse_bilk(reader: StreamReader):
	length = await _parse_integers(reader)
	_ = await reader.read(length)
	await reader.readline()
	return _


async def _parse_arrays(reader: StreamReader):
	_ = []

	length = await _parse_integers(reader)
	if length < 0:
		return _

	for i in range(length):
		_.append(await parse_packet(reader))

	return _


____ = {
	REDIS_SIMPLE: _parse_simple,
	REDIS_ERROR: _parse_error,
	REDIS_INTEGERS: _parse_integers,
	REDIS_BILK: _parse_bilk,
	REDIS_ARRAY: _parse_arrays
}


async def parse_packet(reader: StreamReader):
	flag = await reader.read(1)

	try:
		return await ____[flag](reader)
	except (KeyError, TypeError, ValueError) as e:
		raise RedisPacketError(e)
