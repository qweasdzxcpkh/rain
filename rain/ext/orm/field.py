from rain.ext.orm.utils import escape_string

_default = object()


class _Field(object):
	__slots__ = (
		'name', 'nullable',
		'is_primary', 'unique',
		'default', 'onupdate',
		'index_key'
	)

	sql_type = None

	def __init__(
			self,
			name=None,
			nullable=True, is_primary=False,
			unique=False, default=_default,
			index_key=None, on_update=None
	):
		self.name = name
		self.nullable = nullable
		self.is_primary = is_primary
		self.unique = unique
		self.default = default
		self.index_key = index_key
		self.onupdate = on_update

	def _type_for_create(self):
		return self.sql_type

	def for_create(self):
		_ = ['{} {}'.format(self.name, self._type_for_create())]

		auto_incr = getattr(self, 'auto_increment', False)
		if auto_incr:
			_.append('AUTO INCREMENT')

		if not self.nullable:
			_.append('NOT NULL')

		if self.unique:
			_.append('UNIQUE')

		if self.default is not _default:
			_ += ['DEFAULT', escape_string(str(self.default))]

		if self.onupdate:
			_ += ['ON UPDATE', escape_string(str(self.onupdate))]

		return ' '.join(_)


# INT


class _IntField(_Field):
	__slots__ = (*_Field.__slots__, 'auto_increment')

	def __init__(self, auto_increment=False, **kwargs):
		super().__init__(**kwargs)
		self.auto_increment = auto_increment


class TINYINT(_IntField):
	__slots__ = _IntField.__slots__
	sql_type = 'TINYINT'


BOOLEAN = TINYINT


class SMALLINT(_IntField):
	__slots__ = _IntField.__slots__
	sql_type = 'SMALLINT'


class MEDIUMINT(_IntField):
	__slots__ = _IntField.__slots__
	sql_type = 'MEDIUMINT'


class INT(_IntField):
	__slots__ = _IntField.__slots__
	sql_type = 'INT'


INTEGER = INT


class BIGINT(_IntField):
	__slots__ = _IntField.__slots__
	sql_type = 'BIGINT'


# FLOAT

class _FloatField(_Field):
	__slots__ = (*_Field.__slots__, 'm', 'd')

	def __init__(self, m=None, d=None, **kwargs):
		super().__init__(**kwargs)
		self.m = m
		self.d = d

	def _type_for_create(self):
		if self.m and self.d:
			return '{}({},{})'.format(self.sql_type, self.m, self.d)

		return self.sql_type


class FLOAT(_FloatField):
	__slots__ = _FloatField.__slots__
	sql_type = 'FLOAT'


class DOUBLE(_FloatField):
	__slots__ = _FloatField.__slots__
	sql_type = 'DOUBLE '


class REAL(_FloatField):
	__slots__ = _FloatField.__slots__
	sql_type = 'REAL'


# DECIMAL

class DECIMAL(_FloatField):
	__slots__ = _FloatField.__slots__
	sql_type = 'DECIMAL'


# BIT

class BIT(_Field):
	__slots__ = (*_Field.__slots__, 'm')
	sql_type = 'BIT'

	def __init__(self, m, **kwargs):
		super().__init__(**kwargs)
		self.m = m

	def _type_for_create(self):
		return '{}({})'.format(self.sql_type, self.m)


# Date And Time

class DATE(_Field):
	__slots__ = _Field.__slots__
	sql_type = 'DATE'


class DATETIME(_Field):
	__slots__ = _Field.__slots__
	sql_type = 'DATETIME'


class TIMESTAMP(_Field):
	__slots__ = _Field.__slots__
	sql_type = 'TIMESTAMP'


class TIME(_Field):
	__slots__ = _Field.__slots__
	sql_type = 'TIME'


class YEAR(_Field):
	__slots__ = (*_Field.__slots__, 'length')
	sql_type = 'YEAR'

	def __init__(self, length=None, **kwargs):
		super().__init__(**kwargs)

		self.length = length

	def _type_for_create(self):
		if self.length == 2:
			return '{}(2)'.format(self.sql_type)

		return self.sql_type


# CHAR


class _StringField(_Field):
	__slots__ = (*_Field.__slots__, 'length')

	def __init__(self, length, **kwargs):
		super().__init__(**kwargs)
		self.length = length

	def _type_for_create(self):
		return '{}({})'.format(self.sql_type, self.length)


class CHAR(_StringField):
	__slots__ = _StringField.__slots__
	sql_type = 'CHAR'


class VARCHAR(_StringField):
	__slots__ = _StringField.__slots__
	sql_type = 'VARCHAR'


class BINARY(_StringField):
	__slots__ = _StringField.__slots__
	sql_type = 'BINARY'


class VARBINARY(_StringField):
	__slots__ = _StringField.__slots__
	sql_type = 'VARBINARY'


class BLOB(_Field):
	__slots__ = _Field.__slots__
	sql_type = 'BLOB'


class TEXT(_Field):
	__slots__ = _Field.__slots__
	sql_type = 'TEXT'


class JSON(_Field):
	__slots__ = _Field.__slots__
	sql_type = 'JSON'
