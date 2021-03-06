from sys import stderr
from traceback import print_exc

from rain.utils import FakeTextFile

__g = None


def _imp_g():
	global __g
	from rain import g

	__g = g

	return __g


# noinspection PyMethodMayBeStatic
class RainError(Exception):
	def __init__(self):
		super().__init__(
			'<Error: {}>\n\t{}'.format(
				self.__class__.__name__,
				self.details()
			)
		)

	def details(self):
		return ''


_d = {}


class HTTPError(RainError):
	status = 500

	def __init__(self, res_kwargs=None):
		super().__init__()
		self.res_kwargs = res_kwargs or _d

	def make_response(self, **kwargs):
		for k in self.res_kwargs.keys():
			if k not in kwargs:
				kwargs[k] = self.res_kwargs[k]

		return self.status, None, kwargs


class BadRequestError(HTTPError):
	status = 400


class NotFoundError(HTTPError):
	status = 404


class MethodNotAllowError(HTTPError):
	status = 405


class LengthRequiredError(HTTPError):
	status = 411


class EntityTooLargeError(HTTPError):
	status = 413


class UnsupportedMediaTypeError(HTTPError):
	status = 415


def _error_pretty(msg):
	stderr.write(msg)
	return '<pre style="font-family:  CURSIVE;">{}</pre>'.format(msg)


class ServerError(HTTPError):
	status = 500

	def __init__(self):
		super().__init__()

		self.file = FakeTextFile()
		print_exc(file=self.file)

	def make_response(self, **kwargs):
		s, d, h = super().make_response(**kwargs)
		if _imp_g().debug:
			d = _error_pretty(self.file.read())

		return s, d, h


class TplError(HTTPError):
	status = 500

	def __init__(self, file, lineno, error):
		super().__init__()

		self.file = file
		self.lineno = lineno
		self.error = error

	def make_response(self, **kwargs):
		s, d, h = super().make_response(**kwargs)
		if _imp_g().debug:
			d = _error_pretty(
				'TplFileName: {}; LineNo: {}; Error: {}'.format(
					self.file, self.lineno, self.error
				)
			)

		return s, d, h


class TplParseError(TplError):
	pass


class TplOrderError(TplError):
	def __init__(self, order, error):
		super().__init__(order.pr.name, order.left.line, error)
