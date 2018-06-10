from rain.utils.funcwrap import cachedproperty
from rain.ext.orm.utils import escape


class _WhereSQL(object):
	def __init__(self):
		self.conditions = None

	def where(self, *conditions):
		pass

	def _where(self):
		if self.conditions is None:
			return ' '

		return ' '.join(map(str, self.conditions))


class _GroupBySQL(object):
	def __init__(self):
		self.group = None

	def groupby(self, key):
		pass


class _OrderBySQL(object):
	def __init__(self):
		self.orders = None

	def orderby(self, *keys):
		pass


class _LimitSQL(object):
	def __init__(self):
		self._offset = 0
		self._limit_no = 0

	def limit(self, limit, offset=0):
		self._limit_no = limit
		self._offset = offset

		return self

	def _limit(self):
		if self._limit_no:
			return 'LIMIT {},{}'.format(self._offset, self._limit_no)
		else:
			return ' '


class _ValuesSQL(object):
	def __init__(self):
		self._keys = None
		self._vals = None

	def values(self, lst=None, **kwargs):
		self._vals = []

		if lst:
			_ = lst[0]
			self._keys = _.keys()
			self._vals += list(map(lambda x: map(lambda y: escape(y), x.values()), lst))
		else:
			self._keys = kwargs.keys()
			self._vals.append(map(lambda x: escape(x), kwargs.values()))

		return self

	def _val_txt(self):
		return ','.join(
			map(
				lambda x: '(' + ','.join(x) + ')',
				self._vals
			)
		)


class _SQL(object):
	def __init__(self):
		for cls in self.__class__.mro():
			if cls in {self.__class__, _SQL} or cls is object:
				continue
			cls.__init__(self)

	def render(self):
		raise NotImplementedError


class InsertSQL(_SQL, _ValuesSQL):
	def __init__(self, table, prefix=None, on_duplicate=None):
		super().__init__()

		prefix = (prefix or '').upper()
		assert prefix in {'LOW_PRIORITY', 'DELAYED', 'HIGH_PRIORITY', 'IGNORE', ''}
		self.prefix = ' {} '.format(prefix) if prefix else ' '

		self.table = table
		self.on_duplicate = 'ON DUPLICATE KEY UPDATE {}'.format(on_duplicate) if on_duplicate else ''

	def render(self):
		if self._keys is None or self._vals is None:
			return ''

		return 'INSERT{prefix}INTO {tbl_name} ({cols}) VALUES {vals}{on_dupl}'.format(
			prefix=self.prefix,
			tbl_name=self.table.__table__name__,
			cols=','.join(self._keys),
			vals=self._val_txt(),
			on_dupl=self.on_duplicate
		).strip()


# noinspection SqlDialectInspection
class DeleteSQL(_SQL, _WhereSQL, _OrderBySQL, _LimitSQL):
	def __init__(self, table, prefix=None):
		super().__init__()

		prefix = (prefix or '').upper()
		assert prefix in {'LOW_PRIORITY', 'DELAYED', 'HIGH_PRIORITY', 'IGNORE', ''}
		self.prefix = ' {} '.format(prefix) if prefix else ' '

		self.table = table

	def render(self):
		return 'DELETE{prefix}FROM {tbl_name}{where}{limit}'.format(
			prefix=self.prefix,
			tbl_name=self.table.__table__name__,
			where=self._where(),
			limit=self._limit()
		).strip()


class UpdateSQL(_SQL, _WhereSQL, _OrderBySQL, _LimitSQL, _ValuesSQL):
	def render(self):
		pass

	def __init__(self):
		super().__init__()


class SelectSQL(_SQL, _WhereSQL, _GroupBySQL, _OrderBySQL, _LimitSQL):
	def render(self):
		pass

	def __init__(self):
		super().__init__()


if __name__ == '__main__':
	from rain.ext.orm import field
	from rain.ext.orm.components import Table


	class User(Table):
		__auto_create__ = True

		id = field.INT(is_primary=True, auto_increment=True)
		name = field.CHAR(20, unique=True, index_key='name.unique')
		create_time = field.DATETIME()


	insert = InsertSQL(User)
	insert.values(lst=[{'name': 'select * from, mysql.User', 'id': 12}, {'name': 'sport', 'id': 13}])
	print(insert.render())

	delete = DeleteSQL(User).limit(12)
	print(delete.render())
