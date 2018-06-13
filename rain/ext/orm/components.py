from inspect import isclass
from typing import Type

from rain.ext.orm import field
from rain.ext.orm.error import ORMError


class _Meta(type):
	__pool_class__ = None
	__pool_size__ = 1
	__connection_conf__ = None

	def __new__(mcs, name, bases, attrs):
		table: Type[_Table] = type.__new__(mcs, name, bases, attrs)

		if table.__is_table_class__ and bases[0] != _Table:
			mcs.init_table(table)

		return table

	@classmethod
	def init_table(mcs, table):
		if not table.__table_name__:
			table.__table_name__ = table.__name__

		columns = {}
		indexs = {}
		primary_keys = []

		for k, v in vars(table).items():
			if isinstance(v, field.Field):
				v.set_name(k)
				columns[k] = v

				v.tbl = table

				if v.is_primary:
					primary_keys.append(k)

				if v.index_key:
					if v.index_key in indexs:
						indexs[v.index_key].append(k)
					else:
						indexs[v.index_key] = [k]

		table.__columns__ = columns
		table.__index_keys__ = indexs
		table.__primary_keys__ = primary_keys

		if table.__auto_create__:
			table_sql, index_sqls = render_create_sql(table)


_none = object()


class _Table(object):
	__slots__ = ('__row__',)

	__is_table_class__ = False

	__table_name__ = ''
	__auto_create__ = False
	__columns__ = None
	__index_keys__ = None
	__primary_keys__ = None

	def __init__(self):
		self.__row__ = None

	def set_row(self, row):
		self.__row__ = row


# noinspection SqlDialectInspection,SqlNoDataSourceInspection
def render_create_sql(table):
	assert is_table(table)

	table_name = table.__table_name__

	columns = list(
		map(
			lambda item: '\t' + item[1].for_create(),
			filter(
				lambda item: isinstance(item[1], field.Field),
				table.__columns__.items()
			)
		)
	)

	columns.append('\tPRIMARY KEY({})'.format(', '.join(table.__primary_keys__)))

	table_sql = 'CREATE TABLE IF NOT EXISTS {}(\r\n{}\r\n)'.format(table_name, ',\r\n'.join(columns))
	index_sqls = []

	if table.__index_keys__:
		for name, val in table.__index_keys__.items():
			if '.' in name:
				index_name, *other = name.split('.')
				other = other[:2]

				if len(other) == 2:
					index_create_type, index_type = other
				else:
					other = other[0].upper()
					if other in ['UNIQUE', 'FULLTEXT', 'SPATIAL']:
						index_create_type = other
						index_type = ''
					else:
						index_create_type = ''
						index_type = other
			else:
				index_create_type = index_type = ''
				index_name = name

			index_sqls.append(
				'CREATE {} INDEX {} {} ON {} ({})'.format(
					index_create_type,
					index_name,
					'USING ' + index_type if index_type else '',
					table_name,
					','.join(val)
				)
			)

	return table_sql, index_sqls


def is_table(tbl):
	return isclass(tbl) and tbl is not _Table and _Table in tbl.__mro__ and len(tbl.__mro__) > 3


def make_base(**kwargs) -> Type[_Table]:
	"""
	dynamically adding metaclass
	emmmmmmmmmmmmmmmmmmmm,,,,,,i never wrote this way,,,,,,
	"""

	pool_class = kwargs.pop('pool_class', None)
	pool_size = kwargs.pop('pool_size', 1)

	mcs = type(
		'metaclass',
		(_Meta,),
		{
			'__connection__conf__': kwargs,
			'__pool_class__': pool_class,
			'__pool_size__': pool_size
		}
	)

	class _TableClass(_Table, metaclass=mcs):
		__slots__ = _Table.__slots__
		__is_table_class__ = True

		def __getattribute__(self, item):
			super_value = _Table.__getattribute__(self, item)
			if not isinstance(super_value, field.Field):
				return super_value

			_ = super().__getattribute__('__row__').get(item, _none)
			if _ is _none:
				raise ORMError('table: <{}> : column "{}" is empty'.format(self.__class__.__name__, item))

			return _

	return _TableClass  # type: Type[_Table]


if __name__ == '__main__':
	base = make_base()


	class User(base):
		__auto_create__ = True

		id = field.INT(is_primary=True, auto_increment=True)
		name = field.CHAR(20, unique=True, index_key='name.unique')
		create_time = field.DATETIME()


	class Group(base):
		__auto_create__ = True

		id = field.INT(is_primary=True, auto_increment=True)
		name = field.CHAR(20, unique=True)
		create_time = field.DATETIME()
