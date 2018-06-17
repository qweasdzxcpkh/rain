from decimal import Decimal
from datetime import datetime, timedelta

_datetime_format = '%Y-%m-%d %H:%M:%S'


def escape_string(txt):
	s_in = "'" in txt
	d_in = '"' in txt

	if s_in and d_in:
		return "'" + txt.replace('"', '\\"').replace("'", "\\'") + "'"

	if s_in:
		return '"' + txt + '"'

	return "'" + txt + "'"


def escape_bytes(txt):
	s_in = b"'" in txt
	d_in = b'"' in txt

	if s_in and d_in:
		return b"'" + txt.replace(b'"', b'\\"').replace(b"'", b"\\'") + b"'"

	if s_in:
		return b'"' + txt + b'"'

	return b"'" + txt + b"'"


def escape(val):
	if isinstance(val, (int, float, Decimal)):
		return str(val)

	if isinstance(val, bytes):
		return escape_bytes(val)

	if isinstance(val, str):
		return escape_string(val)

	if isinstance(val, (datetime, timedelta)):
		return escape_string(val.strftime(_datetime_format))

	return escape_string(str(val))


def escape_for_select(val):
	if isinstance(val, bytes):
		return escape_string(val.decode())

	return escape(val)
