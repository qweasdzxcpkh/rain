from rain.ext.orm.escape import escape
from rain.ext.orm.op import OP, Alias
from rain.ext.orm.components import is_table
from rain.ext.orm import field


class _WhereSQL(object):
	def __init__(self):
		self.conditions = None

	def where(self, *conditions):
		if self.conditions:
			self.conditions += list(conditions)
		else:
			self.conditions = list(conditions)

		return self

	def _where(self):
		if self.conditions is None:
			return

		return 'WHERE ' + OP.and_(*self.conditions)


class _OrderBySQL(object):
	def __init__(self):
		self._orders = None

	def orderby(self, *keys):
		if self._orders:
			self._orders += list(map(str, keys))
		else:
			self._orders = list(map(str, keys))

		return self

	def _order(self):
		if not self._orders:
			return

		return 'ORDER BY {}'.format(','.join(self._orders))


class _LimitSQL(object):
	def __init__(self):
		self._offset = 0
		self._limit_no = 0

	def limit(self, limit, offset=0):
		self._limit_no = limit
		self._offset = offset

		return self

	def _limit(self):
		if not self._limit_no:
			return

		return 'LIMIT {},{}'.format(self._offset, self._limit_no)


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
		__ = []
		contain_bytes = False
		for row in self._vals:
			_ = []
			row_contain_bytes = False
			for v in row:
				if isinstance(v, bytes):
					row_contain_bytes = True
				_.append(v)

			if row_contain_bytes:
				__.append(_)
				contain_bytes = True
			else:
				__.append('(' + ','.join(_) + ')')

		return __, contain_bytes


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

		before = 'INSERT{prefix}INTO {tbl_name} ({cols}) VALUES '.format(
			prefix=self.prefix,
			tbl_name=self.table.__table_name__,
			cols=','.join(self._keys)
		)

		vals, contain_bytes = self._val_txt()
		if contain_bytes:
			return b''.join(
				[
					before.encode(),
					b','.join(
						map(
							lambda row: (
								b'('
								+
								b','.join(map(lambda x: x if isinstance(x, bytes) else x.encode(), row))
								+
								b')'

								if
								isinstance(row, list)

								else
								row.encode()
							),
							vals
						)
					),
					self.on_duplicate.encode()
				]
			).strip()

		return '{before}{vals}{on_dupl}'.format(
			before=before,
			vals=','.join(vals),
			on_dupl=self.on_duplicate
		).strip()


class UpdateSQL(_SQL, _WhereSQL, _OrderBySQL, _LimitSQL, _ValuesSQL):
	def __init__(self):
		super().__init__()

	def render(self):
		pass


# noinspection SqlDialectInspection
class DeleteSQL(_SQL, _WhereSQL, _OrderBySQL, _LimitSQL):
	def __init__(self, table, prefix=None):
		super().__init__()

		prefix = (prefix or '').upper()
		assert prefix in {'LOW_PRIORITY', 'DELAYED', 'HIGH_PRIORITY', 'IGNORE', ''}
		self.prefix = ' {} '.format(prefix) if prefix else ' '

		self.table = table

	def render(self):
		_ = filter(bool, [self._where(), self._order(), self._limit()])

		return 'DELETE{prefix}FROM {tbl_name} {ext}'.format(
			prefix=self.prefix,
			tbl_name=self.table.__table_name__,
			ext=' '.join(_)
		).strip()


# noinspection SqlDialectInspection,PyStringFormat
class SelectSQL(_SQL, _WhereSQL, _OrderBySQL, _LimitSQL):
	def __init__(self, *fields, prefix=None, expression=None):
		super().__init__()

		self.tbls = set()
		self.fields = []
		for f in fields:
			if isinstance(f, field.Field):
				self.tbls.add(f.tbl.__table_name__)
				self.fields.append(str(f))
			elif isinstance(f, Alias):
				_f = f.field
				self.tbls.add(_f.tbl.__table_name__)
				self.fields.append(str(f))
			elif isinstance(f, OP):
				_f = f.base
				self.tbls.add(_f.tbl.__table_name__)
				self.fields.append(str(f))

		if not self.fields and is_table(fields[0]):
			self.tbls.add(fields[0].__table_name__)
			self.fields = ['*']

		if not self.fields:
			raise ValueError

		self.fields = ','.join(self.fields)
		self.prefix = prefix
		self.expression = expression

		self._groups = None
		self._having = None

	def having(self, *conditions):
		if self._having:
			self._having += list(map(str, conditions))
		else:
			self._having = list(map(str, conditions))

		return self

	def groupby(self, *keys):
		if self._groups:
			self._groups += list(map(str, keys))
		else:
			self._groups = list(map(str, keys))

		return self

	def _groups_txt(self):
		if not self._groups:
			return

		return 'GROUP BY ' + ','.join(self._groups)

	def _havings_txt(self):
		if not self._having:
			return

		return 'HAVING ' + OP.and_(*self._having)

	def render(self):
		if self.fields == '*' and self.expression is not None:
			return 'SELECT {}'.format(self.expression)

		_ = filter(
			bool,
			[
				self._where(), self._groups_txt(),
				self._havings_txt(), self._order(),
				self._limit()
			]
		)

		return 'SELECT {} FROM {} {}'.format(self.fields, ','.join(self.tbls), ' '.join(_)).strip()
