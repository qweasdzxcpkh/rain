def escape_string(txt):
	if "'" in txt:
		_ = '"{}"'
	else:
		_ = "'{}'"

	return _.format(txt)


def escape_bytes(txt):
	if b"'" in txt:
		return b'"' + txt + b'"'

	return b"'" + txt + b"'"


def escape(val):
	if isinstance(val, bytes):
		return escape_bytes(val)

	if isinstance(val, str):
		return escape_string(val)

	return str(val)
