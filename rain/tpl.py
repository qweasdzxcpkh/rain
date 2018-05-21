import os
from html import escape

from rain.error import TplError, TplOrderError, TplParseError
from rain.utils import AttrDict

__plk__ = object()

DEFAULT_BUILTINS = {
	'str': str, 'escape': escape,
	'int': int, 'hex': hex, 'oct': oct, 'bin': bin,
	'chr': chr, 'ord': ord,
	'range': range,
	'len': len,
	'abs': abs, 'round': round
}


class _OrderSign(object):
	all = {
		'{{': '}}', '}}': '{{',
		'{#': '#}', '#}': '{#',
		'{%': '%}', '%}': '{%'
	}

	def __init__(self, txt, index, line):
		self.txt = txt
		self.index = index
		self.line = line

	def __eq__(self, other):
		if other.__class__ != self.__class__:
			return False

		return self.all[self.txt] == other.txt

	def __repr__(self):
		return str(self.index)


class _Order(object):
	__order__ = ''

	def __init__(self, left, right=None):
		self.left = left
		self.right = right

		self.txt = ''
		self.pr = None
		self.begin_order = None

		self.parent = None
		self.children = []
		self._locals = AttrDict()

	def __repr__(self):
		return '<{0:16} LEFT: {1} RIGHT: {2} TXT: {3} >'.format(
			self.__class__.__name__,
			self.left,
			self.right if self.right else 'W',
			self.txt[:6] + '...' if len(self.txt) >= 10 else self.txt
		)

	@property
	def locals(self):
		if self.parent:
			self._locals.update({__plk__: self.parent.locals or {}})

		return self._locals

	def init(self):
		return self

	def complete(self):
		return self.txt.strip()

	def render(self):
		pass


def _render_children(lst, cs):
	for c in cs:
		if isinstance(c, _Order):
			lst.append(str(c.render()))
		else:
			lst.append(str(c))


def _add_plocal(data, r):
	for k, v in data.items():
		if k != __plk__ and k not in r:
			r[k] = v

	if __plk__ in data:
		_add_plocal(data.pop(__plk__), r)
	return r


def _eval(order: _Order):
	builtins = DEFAULT_BUILTINS.copy()
	if order.pr.config('BUILTINS'):
		for k, v in order.pr.config('BUILTINS').items():
			if k in builtins and v is None:
				if v is None:
					del builtins[k]
			else:
				builtins[k] = v

	data = {} if type(order) is str else order.locals

	d = {'__builtins__': builtins}
	d.update(data)
	d = _add_plocal(d, {})

	try:
		return eval(getattr(order, 'code', getattr(order, 'txt')), d)
	except Exception as E:
		e = E

	if e:
		raise TplParseError(order.pr.name, order.left.line, e)


class _CommentOrder(_Order):
	def render(self):
		if self.pr.config('COMMENTS'):
			return '<!--\n\t{0}\n\t-->'.format(self.txt)

		return ''


class _EndOrder(object):
	__order__ = ''
	all = {'block': 'endblock', 'if': 'endif', 'for': 'endfor'}

	def __init__(self, txt):
		if _EndOrder.all[txt]:
			self.txt = txt

		self.parent = None

	def complete(self):
		pass


class _ExecutableOrder(_Order):
	all = {}
	no_end = ['include', 'extends', 'set', '__import__']

	def __init__(self, left, right=None):
		super().__init__(left, right)

		self.parent = None
		self.blocks = {}

	def init(self):
		od, *txt = self.txt.split(' ')
		self.txt = ' '.join(txt).strip()
		od = od.lower()

		if not od.startswith('end'):
			no = _ExecutableOrder.all[od.lower()](self.left)
			for k, v in vars(self).items():
				setattr(no, k, v)

			return no
		else:
			return _EndOrder(od[3:])


class _UseFileOrder(_ExecutableOrder):
	__parse__ = None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.target_filename = ''

	@classmethod
	def parse(cls, name, config, comeform=None, cache=None):
		if cls.__parse__ is None:
			cls.__parse__ = __import__('tpl.parser.main', fromlist=['parse']).parse

		if callable(cls.__parse__):
			return cls.__parse__(name, config or {}, comeform=comeform, cache=cache)

	def complete(self):
		filename = self.txt
		if filename[0] == filename[-1] and filename[0] in ['"', "'"]:
			filename = filename[1:-1]

		filename = os.path.join(self.pr.config('ROOT'), filename)
		if not os.path.exists(filename):
			raise FileNotFoundError(filename)

		self.target_filename = filename


class _IncludeOrder(_UseFileOrder):
	__order__ = 'include'

	def render(self):
		if self.target_filename == self.pr.name:
			raise TplOrderError(self, 'IncludeSelf Error')

		cf = self.pr.comeform[:]  # **[:]**

		if self.target_filename in cf:
			raise TplOrderError(self, 'Multiple Include Error')

		cf.append(self.pr.name)

		pr = self.parse(
			self.target_filename,
			self.pr.config(),
			comeform=cf,
			cache=self.pr.cache
		)

		return pr.render(self.locals)


class _ExtendsOrder(_UseFileOrder):
	__order__ = 'extends'

	def render(self):
		if self.target_filename == self.pr.name:
			raise TplOrderError(self, 'ExtendSelf Error')

		if not self.pr.base:
			self.pr.base = self.parse(
				self.target_filename,
				self.pr.config(),
				cache=self.pr.cache
			)

		if self.pr.base.name in list(
				map(
					lambda x: x.name,
					self.pr.get_exts()
				)
		):
			raise TplOrderError(self, 'Multiple Extends Error')

		return ''


class _BlockOrder(_ExecutableOrder):
	__order__ = 'block'

	def __init__(self, left, right=None):
		super().__init__(left, right)

	def render(self):
		self.pr.blocks[self.txt] = self.pr.children.index(self)
		return self

	def render_(self):
		cache = []
		_render_children(cache, self.children)
		return ''.join(cache)


class _ForOrder(_ExecutableOrder):
	__order__ = 'for'

	def __init__(self, left, right=None):
		super().__init__(left, right)

		self.loop_vars = []
		self.code = ''

	def complete(self):
		ind = self.txt.find(' in ')
		if ind <= 0:
			raise TplOrderError(self, '<_ForOrder "{0}">'.format(self.txt))

		self.loop_vars = list(
			filter(
				bool,
				map(
					lambda x: x.strip(),
					self.txt[: ind].strip().split(',')
				)
			)
		)

		self.code = self.txt[ind + 4:].strip()

	def render(self):
		loop_base = _eval(self)

		cache = ['']
		length = len(loop_base)
		for ind, item in enumerate(loop_base):
			d = {'loop': {'index': ind, 'length': length}}
			if not getattr(item, '__iter__', None):
				item = [item]

			if len(item) != len(self.loop_vars):
				raise TplOrderError(self, '<_ForOrder "{0}">'.format(self.txt))

			d.update(zip(self.loop_vars, item))

			self._locals.update(AttrDict().init(d))
			_render_children(cache, self.children)

		return ''.join(cache)


class _IfOrder(_ExecutableOrder):
	__order__ = 'if'

	def __init__(self, left, right=None):
		super().__init__(left, right)

		self.elifs = []
		self.else_ = None

	def test(self):
		self.elifs.insert(0, self)

		for to in self.elifs:
			if bool(_eval(to)):
				return to.render(test=True)

		return self.else_.render() if self.else_ else ''

	def render(self, test=False):
		if not test:
			return self.test()

		cache = []
		_render_children(cache, self.children)
		return ''.join(cache)


class _ElOrder(_ExecutableOrder):
	def __init__(self, left, right=None):
		super().__init__(left, right)

		self.if_order = None

	def render(self, test=True):
		cache = []
		_render_children(cache, self.children)
		return ''.join(cache)


class _ElifOrder(_ElOrder):
	__order__ = 'elif'

	def complete(self):
		super().complete()

		self.if_order.elifs.append(self)


class _ElseOrder(_ElOrder):
	__order__ = 'else'

	def complete(self):
		super().complete()

		self.if_order.else_ = self


class _SetOrder(_ExecutableOrder):
	__order__ = 'set'

	def __init__(self, left, right=None):
		super().__init__(left, right)

		self.name = ''
		self.code = ''

	def complete(self):
		ind = self.txt.find('=')
		if ind <= 0:
			raise TplOrderError(self, '<_SetOrder "{0}">'.format(self.txt))

		name = self.txt[: ind].strip()
		code = self.txt[ind + 1:].strip()

		if not name or not code:
			raise TplOrderError(self, '<_SetOrder "{0}">'.format(self.txt))

		self.name = name
		self.code = code

	# noinspection PyProtectedMember
	def render(self):
		if self.parent is self.pr:
			self.parent.locals[self.name] = _eval(self)
		else:
			self.parent._locals[self.name] = _eval(self)

		return ''


class _ImportOrder(_ExecutableOrder):
	__order__ = '__import__'

	def __init__(self, left, right=None):
		super().__init__(left, right)

		self.imports = {}

	def complete(self):
		for name in map(lambda x: x.strip(), self.txt.strip().split(',')):
			if not name:
				continue

			ie = False
			try:
				self.imports[name] = __import__(name)
			except ImportError as e:
				ie = e

			if ie:
				raise TplOrderError(self, ie)

	# noinspection PyProtectedMember
	def render(self):
		if self.parent is self.pr:
			for k, v in self.imports.items():
				self.parent.locals[k] = v
		else:
			for k, v in self.imports.items():
				self.parent._locals[k] = v

		return ''


class _ReplaceOrder(_Order):
	def render(self):
		return _eval(self)


class _ParseResult(object):
	__cache__ = {}

	CONFIG = {
		'ROOT': '',
		'CODING': 'utf8',
		'COMMENTS': True
	}

	def __init__(self, name, config=None, comeform=None, cache=True):
		self.cache = cache
		self.name = name

		self.children = []

		self.locals = AttrDict()

		self._config = config or {}

		self.comeform = comeform or []
		self.base = None

		self.blocks = {}
		self.ext = None

		self._html = None

	def config(self, name=None):
		if name:
			return self._config.get(
				name,
				self.CONFIG.get(name)
			)
		else:
			d = self.CONFIG.copy()

			for k, v in self._config.items():
				d[k] = v

			return d

	def set_config(self, name, val):
		self._config[name] = val

	def get_exts(self):
		exts = []
		pr = self.ext
		while pr:
			exts.append(pr)
			pr = pr.ext

		return exts

	def pre_render(self, data=None):
		if data:
			self.locals = AttrDict().init(data)

		self._html = []
		for c in self.children:
			if isinstance(c, _Order):
				self._html.append(c.render())
			else:
				self._html.append(str(c))

	def render(self, data=None):
		self.locals = AttrDict().init(data or {})

		self.pre_render()
		if not self.base:
			exts = self.get_exts()

			blocks = {}
			for ext in exts:
				for k, v in ext.blocks.items():
					blocks[k] = getattr(ext, '_html')[v]

			for name, block in blocks.items():
				if name not in self.blocks:
					raise TplOrderError(
						block, 'No statement block name <{0}>'.format(name)
					)

				self._html[self.blocks[name]] = block

			cache = []
			for c in self._html:
				if isinstance(c, _BlockOrder):
					cache.append(str(c.render_()))
				else:
					cache.append(str(c))

			return ''.join([(x.render_() if type(x) is _BlockOrder else x) for x in self._html])

		self.base.ext = self
		return self.base.render(self.locals)


class Stack(object):
	def __init__(self, init=None, default_top=None):
		self.init = init or []
		self.default_top = default_top

	@property
	def top(self):
		return self.init[-1] if self.init else self.default_top

	def push(self, item):
		self.init.append(item)

	def pop(self):
		return self.init.pop() if self.init else None

	def __iter__(self):
		return iter(self.init)


def _new_order(oc):
	return {
		'{{': _ReplaceOrder,
		'{#': _CommentOrder,
		'{%': _ExecutableOrder
	}[oc.txt](oc)


def _add_raw_cache(raw, pr, prev_order):
	if not prev_order:
		pr.children.append(raw)
	else:
		if isinstance(
				prev_order,
				(_EndOrder, _ReplaceOrder, _CommentOrder)
		) or prev_order.__order__ in _ExecutableOrder.no_end:
			prev_order.parent.children.append(raw)
		else:
			prev_order.children.append(raw)


def _parse(f, config=None, comeform=None):
	config = config or {}
	root = config.get('ROOT')
	if not os.path.isabs(root):
		raise FileNotFoundError('Tpl Root Must Be A Abs Path')

	f = os.path.join(config.get('ROOT'), f)
	f = os.path.abspath(f)
	if not os.path.exists(f):
		raise FileExistsError(f)

	_pr = _ParseResult.__cache__.get(f)
	if _pr:
		return _pr

	pr = _ParseResult(
		f,
		config,
		comeform=comeform
	)

	with open(f, encoding=pr.config('CODE')) as F:
		parse_stack = Stack(default_top=pr)

		current_order = None
		prev_order = None
		current_quote = None
		current_comment = None
		prev_word = None
		ind = -1
		line_number = 1
		error = None

		order_cache = []
		raw_cache = []

		while True:
			word = F.read(1)
			ind += 1
			if word == '\n':
				line_number += 1

			if not word:
				break

			if current_order:
				order_cache.append(word)
				if word in ['"', "'"]:
					if current_quote:
						if word == current_quote:
							current_quote = None
					else:
						current_quote = word

			if not current_quote:
				if not current_order:
					raw_cache.append(word)

				if not current_comment and prev_word == '{':
					if word in ['%', '{', '#']:
						_add_raw_cache(''.join(raw_cache[:-2]), pr, prev_order)

						raw_cache = []
						current_order = _new_order(_OrderSign('{' + word, ind - 1, line_number))
						if isinstance(current_order, _CommentOrder):
							current_comment = current_order
				elif word == '}':
					if prev_word in ['%', '}', '#']:
						if current_comment and prev_word in ['%', '}']:
							prev_word = word
							continue

						r = _OrderSign(prev_word + '}', ind + 1, line_number)
						if r != current_order.left:
							raise TplParseError(
								f, line_number,
								"<OC Left in line {2}> is '{0}', but <OC Right in line {3}> is '{1}'".format(
									current_order.left.txt, r.txt,
									current_order.left.index, r.index
								)
							)

						if isinstance(current_order, _CommentOrder):
							current_comment = None

						current_order.right = r
						current_order.txt = ''.join(order_cache[:-2]).strip()
						try:
							current_order = current_order.init()
						except KeyError as E:
							error = 'Unsupported _Order <{0}>'.format(str(E)[1:-1])
						if error:
							raise TplParseError(f, line_number, error)

						current_order.pr = pr

						if isinstance(current_order, _ExecutableOrder):
							if type(getattr(current_order, 'children', None)) is list:
								top = parse_stack.top
								top.children.append(current_order)
								current_order.parent = top
								parse_stack.push(current_order)
							else:
								top = parse_stack.top
								current_order.parent = top
								top.children.append(current_order)
						else:
							if isinstance(current_order, _EndOrder):
								begin = parse_stack.pop()
								if begin is None:
									raise TplParseError(
										f, line_number,
										'end{0} has not begin order'.format(current_order.txt)
									)

								if isinstance(begin, _ElOrder):
									while not isinstance(begin, _IfOrder):
										begin = parse_stack.pop()
										if begin is None:
											raise TplParseError(
												f, line_number,
												'endif \'s _IfOrder not found'
											)

								begin.end_order = current_order
								current_order.parent = begin.parent
							else:
								top = parse_stack.top
								current_order.parent = top
								top.children.append(current_order)

						if isinstance(current_order, _ElOrder):
							if_order = current_order.parent
							while not isinstance(if_order, _IfOrder):
								if_order = getattr(if_order, 'if_order', None)
								if if_order is None:
									raise TplParseError(
										f, line_number,
										'<Order: {0}> \'s _IfOrder not found'.format(current_order.__order__)
									)

							current_order.parent.children.remove(current_order)
							current_order.parent = if_order.parent
							current_order.if_order = if_order

						if current_order.__order__ in _ExecutableOrder.no_end:
							parse_stack.pop()

						if isinstance(current_order, _BlockOrder) and current_order.parent is not pr:
							raise TplParseError(f, line_number, '_BlockOrder must be the top of this tpl')

						if current_order.__order__ == 'extends':
							if list(
									filter(
										lambda x: not isinstance(x, str),
										pr.children
									)
							).index(current_order):
								raise TplParseError(f, line_number, '_ExtendsOrder must in the first order')

						current_order.complete()

						order_cache = []
						prev_order = current_order
						current_order = None

			prev_word = word

		_add_raw_cache(''.join(raw_cache), pr, prev_order)

	_ParseResult.__cache__[f] = pr

	return pr


class Tpl(object):
	def __init__(self, name, root, code='utf8', comments=True):
		self.pr = _parse(
			name,
			{'CODING': code, 'ROOT': root, 'COMMENTS': comments}
		)

	def render(self, data, builtins=None):
		self.pr.set_config('BUILTINS', builtins or {})
		return self.pr.render(data)
