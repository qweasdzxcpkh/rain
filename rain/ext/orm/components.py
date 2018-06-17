import asyncio
from inspect import isclass
from typing import Type

from rain.ext.orm import field
from rain.ext.orm.error import ORMError
from rain.ext.mysql.client import Mysql


class _Meta(type):
	__client__ = None
	__client_conf__ = None

	base_table_cls = None  # type: Type[_Table]
	model = None  # type: Type[_Table]

	def __new__(mcs, name, bases, attrs):
		if mcs.__client__ is None:
			mcs._init()

		_table: Type[_Table] = type.__new__(mcs, name, bases, attrs)

		if is_table(_table):
			asyncio.get_event_loop().run_until_complete(
				mcs.init_table(_table)
			)

		return _table

	@classmethod
	async def init_table(mcs, table):
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

			async with mcs.conn_ctx() as conn:
				await conn.create_table(table_sql)
				for index_sql in index_sqls:
					await conn.create_index(index_sql)

	@classmethod
	def _init(mcs):
		mcs.__client__ = Mysql(**mcs.__client_conf__)

	@classmethod
	async def execute(mcs, sql):
		await mcs.__client__.execute(sql)

	@classmethod
	async def query(mcs, sql):
		return await mcs.__client__.query(sql)

	@classmethod
	def conn_ctx(mcs):
		return mcs.__client__.conn_ctx()

	@classmethod
	def tran_ctx(mcs, rollback_on_error=True):
		return mcs.__client__.tran_ctx(rollback_on_error=rollback_on_error)


_none = object()


class _Table(object):
	__slots__ = ('__row__',)

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
	assert is_table(table) and table.__columns__ and table.__primary_keys__

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
						index_create_type = ' '
						index_type = other
			else:
				index_create_type = ' '
				index_type = ''
				index_name = name

			index_sqls.append(
				'CREATE{}INDEX {} {}ON {}({})'.format(
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


def make_base(**kwargs) -> Type[_Meta]:
	mcs: Type[_Meta] = type(
		'metaclass', (_Meta,), {'__client_conf__': kwargs}
	)

	class BaseTableClass(_Table, metaclass=mcs):
		__slots__ = _Table.__slots__

		def __getattribute__(self, item):
			super_value = _Table.__getattribute__(self, item)
			if not isinstance(super_value, field.Field):
				return super_value

			_ = super().__getattribute__('__row__').get(item, _none)
			if _ is _none:
				raise ORMError('table: <{}> : column "{}" is empty'.format(self.__class__.__name__, item))

			return _

	mcs.base_table_cls = mcs.model = BaseTableClass

	return mcs
