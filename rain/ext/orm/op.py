import re

from rain.ext.orm.utils import escape_string

_alias_name_check = re.compile(r'^\w+$')

_default = object()

_str = str


def str(obj):
	if isinstance(obj, _str):
		return escape_string(obj)

	return _str(obj)


class _Fstr(object):
	__slots__ = ('init',)

	def __init__(self, init):
		self.init = init

	def __str__(self):
		return self.init


class Alias(object):
	def __init__(self, field, name):
		assert _alias_name_check.match(name)

		self.field = field
		self.name = name

	def __str__(self):
		return '{} AS {}'.format(self.field, self.name)


class OP(object):
	__slots__ = ('base', 'path')

	def __init__(self, base):
		self.base = base
		self.path = []

	def new(self):
		_ = OP(self.base)
		_.path = self.path[:]
		return _

	def op(self, is_right, ops, other):
		if other is self:
			other = self.new

		new = self.new()
		new.path.append((is_right, ops, other))
		return new

	def __add__(self, other):
		return self.op(0, '+', other)

	def __eq__(self, other):
		return self.op(0, '=', other)

	def __floordiv__(self, other):
		return self.op(0, '//', other)

	def __ge__(self, other):
		return self.op(0, '>=', other)

	def __gt__(self, other):
		return self.op(0, '>', other)

	def __invert__(self):
		return self.op(1, '~', _default)

	def __le__(self, other):
		return self.op(0, '<=', other)

	def __lt__(self, other):
		return self.op(0, '<', other)

	def __lshift__(self, other):
		return self.op(0, '<<', other)

	def __mod__(self, other):
		return self.op(0, '%', other)

	def __mul__(self, other):
		return self.op(0, '*', other)

	def __neg__(self):
		return self.op(1, '-', _default)

	def __ne__(self, other):
		return self.op(0, '!=', other)

	def __radd__(self, other):
		return self.op(1, '+', other)

	def __rfloordiv__(self, other):
		return self.op(1, '//', other)

	def __rlshift__(self, other):
		return self.op(1, '<<', other)

	def __rmod__(self, other):
		return self.op(1, '%', other)

	def __rmul__(self, other):
		return self.op(1, '*', other)

	def __rrshift__(self, other):
		return self.op(1, '>>', other)

	def __rshift__(self, other):
		return self.op(0, '>>', other)

	def __rsub__(self, other):
		return self.op(1, '-', other)

	def __rtruediv__(self, other):
		return self.op(1, '/', other)

	def __sub__(self, other):
		return self.op(0, '-', other)

	def __truediv__(self, other):
		return self.op(0, '/', other)

	def __and__(self, other):
		return self.op(0, '&', other)

	def __rand__(self, other):
		return self.op(1, '&', other)

	def __or__(self, other):
		return self.op(0, '|', other)

	def __ror__(self, other):
		return self.op(1, '|', other)

	def __rxor__(self, other):
		return self.op(1, '^', other)

	def __xor__(self, other):
		return self.op(0, '^', other)

	def alias(self, name):
		return Alias(self.base, name)

	def in_(self, *seq):
		return self.op(
			0, ' IN ', _Fstr('(' + ','.join(map(str, seq)) + ')')
		)

	def between(self, left, right):
		return self.op(
			0, ' BETWEEN ', _Fstr('{} AND {}'.format(*map(str, (left, right))))
		)

	IN = in_

	def __str__(self):
		_ = str(self.base)

		for is_r, ops, other in self.path:
			if other is _default:
				other = ''
			else:
				other = str(other)

			if is_r:
				_ = ''.join(['(', other, ops, _, ')'])
			else:
				_ = ''.join(['(', _, ops, other, ')'])

		return _

	@classmethod
	def and_(cls, *ops):
		return ' AND '.join(map(_str, ops))

	@classmethod
	def or_(cls, *ops):
		return ' OR '.join(map(_str, ops))


if __name__ == '__main__':
	class A(object):

		def __init__(self, name, prefix=None):
			self.prefix = prefix or self.__class__.__name__
			self.name = name

		def __str__(self):
			return '{}.{}'.format(self.prefix, self.name)


	Aid = OP(A('id'))

	print((Aid > 12) == (Aid < 12))
	print(~Aid)
	print(-Aid)
	print(OP.and_(Aid > 12, Aid < 233))
	print(Aid.in_((1, 2, 3)))
	print(Aid.between(12, 45))

	Aname = OP(A('name'))
	print(Aname == 'spring')

	Adate = OP(A('date'))
	print(Adate.between('2018-06-15 01:00:00', '2018-18-12 12:12:12'))
