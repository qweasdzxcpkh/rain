REDIS_SIMPLE = int.from_bytes(b'+', 'little')
REDIS_ERROR = int.from_bytes(b'-', 'little')
REDIS_INTEGERS = int.from_bytes(b':', 'little')
REDIS_BILK = int.from_bytes(b'$', 'little')
REDIS_ARRAY = int.from_bytes(b'*', 'little')


def utf8(s):
	s = str(s)

	h = s[0]
	t = s[-1]
	e = ' ' in s

	_ = None

	if h == t:
		if h == '"':
			_ = "'{}'".format(s)
		elif h == "'":
			_ = '"{}"'.format(s)

	if _ is None and e:
		_ = "'{}'".format(s)

	return (_ or s).encode()


def to_bytes(obj):
	return str(obj).encode('utf8')


def _parse_simple(data):
	return data.strip().decode('latin1')


def _parse_error(data):
	return data.strip().decode('utf8')


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
