import os
from inspect import isclass

from rain.error import NotFoundError, MethodNotAllowError
from rain.utils.load import load_views
from rain.utils.color import Color


def _ext_dict(d: dict, level: int, lst: list):
	for k in sorted(d.keys()):
		v = d[k]
		k = '/' + k
		if isinstance(v, dict):
			lst.append((level, k, ':'))
			_ext_dict(v, level + 1, lst)
			continue

		lst.append((level, k, v))


def _tab(x):
	if x[0] == 0:
		__ = '>' * 40 + '<' * 40
		return '\n{}\n{}\n{}\n|'.format(__, x[1], __)

	level, path, cls = x
	if cls == ':':
		return '|{}{} :'.format('\t' * level * 2, path)

	cls = str(cls)

	_ = ' ' * level * 6
	__ = 79 - len(_) - len(path) - len(cls)

	return '|{}{}{}{}'.format(_, path, ' ' * __, Color(cls).fg(Color.GREEN))


class BaseRouter(object):
	def __init__(self, view_paths, vmap_case='00', find_map_func=None):
		self.maps = {}
		self.view_path = view_paths
		self.vmap_case = vmap_case
		self.find_map = find_map_func if callable(find_map_func) else lambda x: list(self.maps.values())[0]

		self.tpl_dir_path = None

	def load(self):
		for vp in self.view_path:
			name = vp['name']
			vp = vp['path']

			m = {}
			if not os.path.isabs(vp):
				vp = os.path.abspath(vp)
			vdn = os.path.dirname(vp)
			vn = vp[len(vdn) + 1:]
			load_views(vn, dir_path=vdn, m=m)
			self.maps[name] = m

		if len(self.maps) < 2:
			self.vmap_case = '00'

		return self

	def _find_view(self, request):
		m = self.find_map(request)  # type: dict
		if not m:
			raise NotFoundError()

		_ = list(filter(bool, request.path.split('/')))
		prev_m = None
		ind = -1
		for ind, p in enumerate(_):
			prev_m = m
			m = m.get(p)
			if m is None or isclass(m):
				return m, _[ind:], prev_m

		return m, _[ind:], prev_m

	def find_handler(self, request, raise_error=False):
		view, ps, prev_v = self._find_view(request)

		if isinstance(view, dict):
			view = view.get('')

		if isinstance(prev_v, dict):
			prev_v = prev_v.get('')

		if view is None and prev_v is None:
			request.parse_error = NotFoundError()
			return

		if isclass(view):
			ps = False

		if view is None:
			view = prev_v

		instance = view(
			request=request,
			tpl_dir_path=self.tpl_dir_path
		)

		if ps and not instance.ptails:
			if raise_error:
				raise NotFoundError()
			else:
				request.parse_error = NotFoundError()
			return

		handler = getattr(instance, request.method.lower(), None)
		if not callable(handler):
			if raise_error:
				raise MethodNotAllowError()
			else:
				request.parse_error = MethodNotAllowError()
			return

		return handler

	def render(self):
		_ = []
		level = 0

		for vn in sorted(self.maps.keys()):
			_.append((level, '| MAP NAME: {}'.format(Color(vn).fg(Color.YELLOW))))
			_ext_dict(self.maps[vn], 1, _)

		return '\n{}\n{}\n'.format(
			'\n'.join(map(_tab, _)),
			'_' * 80
		)
