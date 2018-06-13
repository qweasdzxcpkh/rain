from inspect import isclass

from rain.ext.orm import field
from rain.ext.orm.error import ORMError


class Meta(type):
	__client__ = None

	def __new__(mcs, name, bases, attrs):
		table: Table = type.__new__(mcs, name, bases, attrs)

		if bases[0] is not object and Table in bases:
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
			pass

	@classmethod
	def set_client(mcs):
		pass


_none = object()


class Table(object, metaclass=Meta):
	__table_name__ = ''
	__auto_create__ = False
	__columns__ = None
	__index_keys__ = None
	__primary_keys__ = None

	def __init__(self):
		self.__row__ = None

	def set_row(self, row):
		self.__row__ = row

	def __getattribute__(self, item):
		super_value = super().__getattribute__(item)
		if not isinstance(super_value, field.Field):
			return super_value

		_ = super().__getattribute__('__row__').get(item, _none)
		if _ is _none:
			raise ORMError('table: <{}> : column "{}" is empty'.format(self.__class__.__name__, item))

		return _


# noinspection SqlDialectInspection,SqlNoDataSourceInspection
def render_create_sql(table):
	assert table is not Table and isclass(table) and Table in table.__mro__
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
	return isclass(tbl) and tbl is not Table and Table in tbl.__mro__


if __name__ == '__main__':
	class User(Table):
		__auto_create__ = True

		id = field.INT(is_primary=True, auto_increment=True)
		name = field.CHAR(20, unique=True, index_key='name.unique')
		create_time = field.DATETIME()


	print(User.id.op >= 12)
