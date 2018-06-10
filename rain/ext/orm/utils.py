from decimal import Decimal


def escape_string(txt):
	if '"' in txt:
		_ = "'{}'"
	else:
		_ = '"{}"'

	return _.format(txt)


def escape_bytes(txt):
	return escape_string(str(txt)[2:-1])


def escape(val):
	if isinstance(val, bytes):
		return escape_bytes(val)

	if isinstance(val, (int, float, Decimal)):
		return str(val)

	if isinstance(val, str):
		return escape_string(val)

	return escape_string(str(val))
