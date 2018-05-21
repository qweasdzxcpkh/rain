import random

_ = [
	'BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE'
]

__ = [
	'LBLACK', 'LRED', 'LGREEN', 'LYELLOW', 'LBLUE', 'LMAGENTA', 'LCYAN', 'LWHITE'
]


def _get_color_num(is_fore, name):
	if name == 'RANDOM':
		name = random.choice(random.choice([_, __]))

	if name in _:
		c = (30 if is_fore else 40) + _.index(name)
	elif name in __:
		c = (90 if is_fore else 100) + __.index(name)
	else:
		raise ValueError('Unknown Color Name: {}'.format(name))

	return c


class Color(str):
	RANDOM = 'RANDOM'

	BLACK = _[0]
	RED = _[1]
	GREEN = _[2]
	YELLOW = _[3]
	BLUE = _[4]
	MAGENTA = _[5]
	CYAN = _[6]
	WHITE = _[7]

	LBLACK = __[0]
	LRED = __[1]
	LGREEN = __[2]
	LYELLOW = __[3]
	LBLUE = __[4]
	LMAGENTA = __[5]
	LCYAN = __[6]
	LWHITE = __[7]

	def __init__(self, raw):
		super().__init__()
		self._fg = 0
		self._bg = 0

	def __str__(self):
		return '\033[{fg}m\x1b[{bg}m{s}\033[0m'.format(
			fg=self._fg,
			bg=self._bg,
			s=super().__str__()
		)

	def bg(self, color):
		self._bg = _get_color_num(False, color)
		return self

	def fg(self, color):
		self._fg = _get_color_num(True, color)
		return self
