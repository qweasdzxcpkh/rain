import time
import json
from http import HTTPStatus

from rain.form import FormFiles, FormData, FormFile, HashFormFile
from rain.utils.funcwrap import cachedproperty

http_status = dict(
	map(
		lambda x: (x.value, (x.name.replace('_', ' '), x.phrase)),
		map(
			lambda x: getattr(HTTPStatus, x),
			filter(
				lambda x: x.isupper(),
				dir(HTTPStatus)
			)
		)
	)
)

_l = tuple()
_real_none = object()


class Cookie(dict):
	__slots__ = ('appends', 'removes')

	def __init__(self):
		super().__init__()
		self.appends = None
		self.removes = None

	def add(self, name, val, path='/', domain=None, max_age=0, secure=False, httponly=False):
		if self.appends is None:
			self.appends = {}

		_ = ['{}={}'.format(name, val), 'Path=' + path]
		if domain:
			_.append('Domain=' + domain)

		if max_age:
			_.append('Max-Age={}'.format(max_age))

		if secure:
			_.append('Secure')

		if httponly:
			_.append('HttpOnly')

		self.appends[name] = '; '.join(_)

	def remove(self, name):
		if self.appends and name in self.appends:
			del self.appends[name]
			return

		if name not in self:
			return

		if self.removes is None:
			self.removes = {}

		self.removes[name] = name + '=;Path=/;Expires=Thu, 01 Jan 1970 00:00:00 GMT'

	@classmethod
	def load(cls, string):
		d = cls()
		if not string:
			return d

		for k, *v in map(lambda x: x.split('='), string.split('; ')):
			if k in d:
				continue
			d[k] = '='.join(v)

		return d


def _mp_parse(lines, boundary, hash_method=''):
	form = FormData()
	files = FormFiles()
	file_cls = HashFormFile if hash_method else FormFile

	if not boundary or not lines:
		return form, files

	begin = ('--' + boundary).encode('latin1') + b'\r\n'
	end = ('--' + boundary + '--').encode('latin1') + b'\r\n'

	file_list = []
	current_file = None
	in_file_description = False

	for line in lines:
		if line == end:
			break

		if line == begin:
			in_file_description = True
			if current_file:
				current_file.write_last_line()
				file_list.append(current_file)
				current_file = file_cls()
				current_file.set_hash_method(hash_method)
			else:
				current_file = file_cls()
				current_file.set_hash_method(hash_method)
			continue

		if in_file_description:
			if line == b'\r\n':
				current_file.parse_description()
				in_file_description = False
				continue

			line = line.decode('utf8', 'ignore')
			ind = line.index(':')
			current_file.headers[line[:ind].strip().lower()] = line[ind + 1:].strip()
		else:
			current_file.write(line)

	current_file.write_last_line()
	file_list.append(current_file)

	for f in file_list:
		if not f.form_name:
			continue

		if not f.file_name:  # normal input field
			data = f.read().decode('utf8', 'ignore')
			if f.form_name in form:
				form[f.form_name].append(data)
			else:
				form[f.form_name] = [data]
		else:  # file input
			if f.form_name in files:
				files[f.form_name].append(f)
			else:
				files[f.form_name] = [f]

	return form, files


class Request(object):
	__slots__ = (
		'hv', 'method', 'path', 'handler',
		'query_string', '_boundary', 'time',
		'headers', '_remote', '_f', '_body_lines',
		'_body_length', '_form_files',
		'_form_data', 'parse_error', 'file_hash_method'
	)

	remote_addr_key = None

	def __init__(self):
		self.time = time.time()

		self.handler = None
		self.hv = None
		self.method = None
		self.path = None
		self.query_string = None

		self.headers = {}
		self.file_hash_method = ''

		self._remote = None

		self._f = False
		self._body_lines = None
		self._body_length = 0
		self._boundary = None
		self._form_files = _real_none
		self._form_data = _real_none

		self.parse_error = None

	def __repr__(self):
		return '<{} {} {} {}>'.format(self.__class__.__name__, self.remote_addr, self.method, self.path)

	@property
	def remote_addr(self):
		if self.remote_addr_key:
			return self.headers.get(self.remote_addr_key) or self._remote

		return self._remote

	@remote_addr.setter
	def remote_addr(self, r):
		self._remote = r

	@cachedproperty
	def content_length(self):
		return self.headers.get('content-length', None)

	@property
	def content_type(self):
		return self.headers.get('content-type', '').split('/')[-1]

	@cachedproperty
	def query(self):
		return FormData.load(self.query_string)

	@cachedproperty
	def keepalive(self):
		return self.headers.get('connection').lower() == 'keep-alive' and self.hv > '1.0'

	@cachedproperty
	def cookie(self) -> Cookie:
		return Cookie.load(self.headers.get('cookie'))

	@cachedproperty
	def form(self):
		ct = self.content_type

		if ct == 'json':
			_ = b''.join(self._body_lines or _l)
			self._form_files = None
			return json.loads(_)
		elif ct == 'plain':
			_ = b''.join(self._body_lines or _l)
			self._form_files = None
			return _.decode('utf8', 'ignore')
		elif ct == 'x-www-form-urlencoded':
			_ = b''.join(self._body_lines or _l)
			self._form_files = None
			return FormData.load(_.decode('latin1', 'ignore'))
		else:  # form-data
			if self._form_data is _real_none:
				self._form_data, self._form_files = _mp_parse(self._body_lines, self._boundary, self.file_hash_method)
				del self._body_lines

			return self._form_data

	@cachedproperty
	def files(self):
		if self._form_files is _real_none:
			getattr(self, 'form')

		return self._form_files


class Response(object):
	__slots__ = (
		'time', 'status', 'headers', 'cookie',
		'body', 'empty', 'req'
	)

	def __init__(self, status, headers=None, cookie=None, body=None, empty=False):
		self.time = -1

		self.status = status
		self.headers = headers or {}
		self.req: Request = None

		self.cookie = cookie  # type: Cookie

		self.body = body
		self.empty = empty

	def __repr__(self):
		return '<{} {}>'.format(self.__class__.__name__, self.status)

	def to_bytes(self):
		self.time = time.time()

		_ = http_status[self.status]
		reason = _[0]
		if self.body is None:
			self.body = _[1]

		if self.empty:
			self.body = b''

		_b = None
		if self.body is not None:
			if isinstance(self.body, bytes):
				_b = self.body
			else:
				self.body = str(self.body)
				_b = self.body.encode('utf8', 'ignore')

			self.headers['Content-Length'] = len(self.body)

		_ = ['HTTP/{} {} {}'.format(self.req.hv, self.status, reason)]
		self.headers['Connection'] = self.req.headers.get('connection')
		_ += list(map(lambda item: '{}: {}'.format(*item), self.headers.items()))

		if self.cookie is not None:
			if self.cookie.appends:
				_ += list(map(lambda x: 'Set-Cookie: {}'.format(x), self.cookie.appends.values()))

			if self.cookie.removes:
				_ += list(map(lambda x: 'Set-Cookie: {}'.format(x), self.cookie.removes.values()))

		_ = list(map(lambda x: x.encode('latin1', 'ignore'), _))
		_.append(b'')
		if _b is not None:
			_.append(_b)

		return b'\r\n'.join(_)

	@classmethod
	def json(cls, data, status=200, cookie=None, ensure_ascii=False, dump_cls=None):
		return cls(
			status,
			cookie=cookie,
			body=json.dumps(data, ensure_ascii=ensure_ascii, cls=dump_cls),
			headers={'Content-Type': 'application/json'}
		)

	@classmethod
	def html(cls, html, status=200, cookie=None):
		return cls(status, body=html, cookie=cookie, headers={'Content-Type': 'text/html'})

	@classmethod
	def make_res(cls, res, status=200, headers=None):
		if not isinstance(res, Response):
			status = status
			body = res
			headers = headers or {}

			if isinstance(res, tuple):
				status, *others = res
				if len(others) == 2:
					body, headers = others

			res = Response(status, body=body, headers=headers)

		return res
