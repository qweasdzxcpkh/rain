from rain.tpl import Tpl
from rain.h2tp import Request, Response


def _reset_to_none(fn):
	return None


class BaseView(object):
	name = NAME = None  # type: str
	active = ACTIVE = True

	tpl_dir_path = None

	def __init__(self, request, tpl_dir_path):
		self.request = request  # type: Request
		self._tpl_dir_path = tpl_dir_path  # type: str

	@_reset_to_none
	def ptails(self, ptails):
		pass

	@_reset_to_none
	def get(self, **kwargs):
		pass

	@_reset_to_none
	def post(self, **kwargs):
		pass

	@_reset_to_none
	def put(self, **kwargs):
		pass

	@_reset_to_none
	def options(self, **kwargs):
		pass

	@_reset_to_none
	def head(self, **kwargs):
		pass

	def render(self, name, data, status=200):
		return Response(
			status,
			body=Tpl(name=name, root=self.tpl_dir_path or self._tpl_dir_path).render(data)
		)
