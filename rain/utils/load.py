import os
import sys
from inspect import ismodule, isclass

from rain.view import BaseView


def _set_views(m, vv):
	if not isclass(vv):
		return

	__ = list(vv.__mro__)
	if BaseView in __ and __.index(BaseView) > 0:
		if not vv.active and not vv.ACTIVE:
			return

		p = vv.name or vv.NAME or ''

		m[p] = vv


def load_views(name, dir_path=None, m=None):
	sys.path.insert(0, dir_path)

	current_path = os.path.join(dir_path, name)
	init_file = os.path.join(current_path, '__init__.py')

	if not os.path.exists(init_file) and not os.path.isfile(init_file):
		return

	fromlist = ['*']
	subms = {}
	for n in os.listdir(current_path):
		abs_n = os.path.join(current_path, n)
		if os.path.isdir(abs_n):
			if '.' in n or n[0] in ['.', '_']:
				continue

			sub_m = {}
			load_views(n, current_path, m=sub_m)
			subms[n] = sub_m
		else:
			if not n.endswith('.py'):
				continue
			else:
				n = '.'.join(n.split('.')[:-1])
				if '.' in n or n[0] in ['_', '.']:
					continue
				fromlist.append(n)

	try:
		package = __import__(name, fromlist=fromlist)
	except ModuleNotFoundError:
		return None

	for k, v in subms.items():
		m[k] = v

	for k in dir(package):
		v = getattr(package, k)
		if ismodule(v):
			_m = {}
			for _ in dir(v):
				_set_views(_m, getattr(v, _))
			if _m:
				m[k] = _m
		else:
			_set_views(m, v)

	sys.path.remove(dir_path)

	return m
