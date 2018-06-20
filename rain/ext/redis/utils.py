from rain.utils.escape import escape_string

__error_cls = None


def _import_error_cls():
	global __error_cls
	if __error_cls is None:
		from rain.ext.redis.base import RedisError

		__error_cls = RedisError

	return __error_cls


REDIS_SIMPLE = int.from_bytes(b'+', 'little')
REDIS_ERROR = int.from_bytes(b'-', 'little')
REDIS_INTEGERS = int.from_bytes(b':', 'little')
REDIS_BILK = int.from_bytes(b'$', 'little')
REDIS_ARRAY = int.from_bytes(b'*', 'little')


def escape(s):
	if isinstance(s, bytes):
		return s

	return escape_string(str(s)).encode()


def _parse_simple(data):
	return data.strip().decode('latin1')


def _parse_error(data):
	raise _import_error_cls()(
		data.strip().decode('utf8')
	)


def _parse_integers(data):
	return int(data.strip())


def _parse_bilk(data):
	ind = data.find(b'\r\n')
	length = int(data[:ind])

	if length < 0:
		return None

	return data[ind + 2: ind + 2 + length]


def _parse_arrays(data):
	ind = data.find(b'\r\n')
	length = int(data[:ind])

	if length < 0:
		return None

	_ = []
	is_bilk = False
	for item in data[ind + 2:].strip().split(b'\r\n'):
		if is_bilk:
			_.append(item)
			is_bilk = False
			continue

		if item[0] == REDIS_BILK:
			is_bilk = True
			if int(item[1:]) < 0:
				_.append(None)
				is_bilk = False
			continue

		if item[0] == REDIS_INTEGERS:
			_.append(int(item[1:]))
			continue

	return _


__ = {
	REDIS_SIMPLE: _parse_simple,
	REDIS_ERROR: _parse_error,
	REDIS_INTEGERS: _parse_integers,
	REDIS_BILK: _parse_bilk,
	REDIS_ARRAY: _parse_arrays
}


def parse_packet(data):
	return __[data[0]](data[1:])
