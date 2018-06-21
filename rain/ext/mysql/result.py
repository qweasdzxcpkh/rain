class _Row(object):
	def __init__(self):
		pass

	def append(self, field, value):
		pass


class ListRow(_Row, list):
	def append(self, field, value):
		list.append(self, value)


class DictRow(_Row, dict):
	def append(self, field, value):
		self[field.name] = value


class QueryResult(object):
	row_class = DictRow

	__slots__ = ('fields_count', 'fields', 'rows', 'field_names')

	def __init__(self):
		self.fields_count = None
		self.fields = None
		self.rows = None

		self.field_names = None
