from decimal import Decimal

from rain.ext.mysql.constants import FIELD_TYPE


class TimeBytes(bytes):
	def __str__(self):
		return self.decode('ascii')


TO_STRING = -1

mysql_decoders = {
	FIELD_TYPE.BIT: None,
	FIELD_TYPE.TINY: int,
	FIELD_TYPE.SHORT: int,
	FIELD_TYPE.LONG: int,
	FIELD_TYPE.FLOAT: float,
	FIELD_TYPE.DOUBLE: float,
	FIELD_TYPE.LONGLONG: int,
	FIELD_TYPE.INT24: int,
	FIELD_TYPE.YEAR: int,
	FIELD_TYPE.TIMESTAMP: None,
	FIELD_TYPE.DATETIME: None,
	FIELD_TYPE.TIME: None,
	FIELD_TYPE.DATE: None,
	FIELD_TYPE.SET: lambda x: set(x.split(b',')),
	FIELD_TYPE.BLOB: None,
	FIELD_TYPE.TINY_BLOB: None,
	FIELD_TYPE.MEDIUM_BLOB: None,
	FIELD_TYPE.LONG_BLOB: None,
	FIELD_TYPE.STRING: TO_STRING,
	FIELD_TYPE.VAR_STRING: TO_STRING,
	FIELD_TYPE.VARCHAR: TO_STRING,
	FIELD_TYPE.DECIMAL: TO_STRING,
	FIELD_TYPE.NEWDECIMAL: Decimal
}
