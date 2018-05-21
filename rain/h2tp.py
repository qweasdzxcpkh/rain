import asyncio
import os
import json
import time
from io import BytesIO
from http import HTTPStatus
from urllib.parse import unquote

from rain.error import HTTPError, BadRequestError, UnsupportedMediaTypeError, LengthRequiredError, EntityTooLargeError
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

max_request_wait_length = 15  # s

max_protocol_keep_alive_length = 15

max_content_length = 16 * 1024 * 1024  # 16MB

request_content_types = {
	'text/xml',
	'text/plain',
	'text/json',
	'application/json',
	'application/x-www-form-urlencoded',
	'multipart/form-data'
}

support_methods = {'GET', 'POST', 'OPTIONS', 'HEAD', 'DELETE', 'PUT'}


class Cookie(dict):
	def __init__(self):
		super().__init__()
		self.a = None
		self.r = None

	def add(self, name, val, path='/', domain=None, max_age=0, secure=False, httponly=False):
		if self.a is None:
			self.a = {}

		_ = ['{}={}'.format(name, val), 'Path=' + path]
		if domain:
			_.append('Domain=' + domain)

		if max_age:
			_.append('Max-Age={}'.format(max_age))

		if secure:
			_.append('Secure')

		if httponly:
			_.append('HttpOnly')

		self.a[name] = '; '.join(_)

	def remove(self, name):
		if self.a and name in self.a:
			del self.a[name]
			return

		if name not in self:
			return

		if self.r is None:
			self.r = {}

		self.r[name] = name + '=;Path=/;Expires=Thu, 01 Jan 1970 00:00:00 GMT'

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


_ln = [None]
_l = []


class FormData(dict):
	@classmethod
	def load(cls, string):
		d = cls()

		for k, *v in map(lambda x: x.split('='), string.split('&')):
			v = unquote('='.join(v))
			if k in d:
				d[k].append(v)
			else:
				d[k] = [v]

		return d

	def get(self, k):
		return super().get(k, _ln)[0]

	def getlst(self, k):
		return super().get(k, _l)


class FormFile(BytesIO):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.form_name = ''
		self.file_name = ''

		self.headers = {}

		self.size = 0

		self.is_overflow = False
		self.__prev_line = None

	def __repr__(self):
		return '<FormFile {0}="{1}">'.format(self.form_name, self.file_name)

	def parse_description(self):
		description = self.headers.get('content-disposition')
		if not description:
			raise ValueError

		d, quote, ck, _ = {}, None, None, ''
		for w in description:
			if quote:
				if w == quote:
					quote = None
				else:
					_ += w
			else:
				if w in ['"', "'"]:
					quote = w
				elif w == '=':
					ck = _.strip().split(' ')[-1]
					_ = ''
				elif w == ';':
					d[ck] = _
					_ = ''
				else:
					_ += w
		d[ck] = _

		self.form_name = d.get('name')
		self.file_name = d.get('filename', '').replace('/', '')

		del d

	def save(self, path, overwrite=True):
		if not overwrite and os.path.exists(path):
			raise ValueError

		self.seek(0)
		with open(path, 'wb') as f:
			for l in self:
				f.write(l)

		self.close()
		return path

	def _write(self, l):
		super().write(l)
		self.size += len(l)

	def write(self, data):
		if self.__prev_line:
			self._write(self.__prev_line)
			self.__prev_line = None

		self.__prev_line = data

	def write_last_line(self):
		self._write(self.__prev_line[:-2])
		self.seek(0)


class FormFiles(dict):
	def get(self, k):
		return super().get(k, _ln)[0]

	def getlst(self, k):
		return super().get(k, _l)


class Request(object):
	__slots__ = (
		'hv', 'method',
		'path', 'handler',
		'query_string',
		'_boundary', 'time',
		'headers', '_remote',
		'_f', '_body_lines',
		'_body_length',
		'_form_files',
		'_form_data',
		'parse_error'
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
		self._remote = None

		self._f = False
		self._body_lines = None
		self._body_length = 0
		self._boundary = None
		self._form_files = None
		self._form_data = None

		self.parse_error = None

	def __repr__(self):
		return '<{} {} {}>'.format(self.__class__.__name__, self.method, self.path)

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
		return self.headers.get('content-length', 0)

	@property
	def content_type(self):
		return self.headers.get('content-type', '').split('/')[-1]

	@cachedproperty
	def query(self):
		return FormData.load(self.query_string)

	@cachedproperty
	def cookie(self) -> Cookie:
		return Cookie.load(self.headers.get('cookie'))

	@cachedproperty
	def form(self):
		if self.method not in {'POST', 'PUT', 'OPTIONS'}:
			return None

		_ = b''.join(self._body_lines)
		ct = self.content_type

		if ct == 'json':
			return json.loads(_)
		elif ct == 'plain':
			return _.decode('utf8', 'ignore')
		elif ct == 'x-www-form-urlencoded':
			return FormData.load(_.decode('latin1', 'ignore'))
		else:  # form-data
			if self._form_data is None:
				self._form_data, self._form_files = _mp_parse(self._body_lines, self._boundary)
				del self._body_lines

			return self._form_data

	@cachedproperty
	def files(self):
		if self.method not in {'POST', 'PUT', 'OPTIONS'}:
			return None

		if self._form_files is None:
			self._form_data, self._form_files = _mp_parse(self._body_lines, self._boundary)
			del self._body_lines
		return self._form_files


def _parse_first_line(line):
	_ = line.decode('latin1', 'ignore').split(' ')
	if len(_) != 3:
		return

	method, qs, hv = _
	i = qs.find('?')
	if i > -1:
		q = qs[:i]
		s = qs[i + 1:]
	else:
		q = qs
		s = None

	return method.upper(), q, s, hv.rstrip()


def _parse_header_line(line, req):
	line = line.decode('latin1', 'ignore')
	i = line.find(':')
	if i > -1:
		k = line[:i].lower()
		v = line[i + 1:].strip()
	else:
		k = line.strip().lower()
		v = ''

	if k == 'content-type':
		v = v.lower()
		if v.startswith('multipart/form-data'):
			v, *b = v.split('; ')
			req._boundary = '; '.join(b)[9:]

		if v not in request_content_types:
			raise UnsupportedMediaTypeError()
	elif k == 'content-length':
		if not v.isdigit() and req.method in {'PUT', 'POST', 'OPTIONS'}:
			raise LengthRequiredError()
		v = int(v)
		if v > max_content_length:
			raise EntityTooLargeError()

	req.headers[k] = v


def _mp_parse(lines, boundary):
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
				current_file = FormFile()
			else:
				current_file = FormFile()
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

	form = FormData()
	files = FormFiles()

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


class HTTPProtocol(asyncio.Protocol):
	def __init__(self, app=None):
		self.app = app
		self.router = app.router
		self.vmap_case = self.router.vmap_case
		self.transport = None
		self.request = None  # type: Request

		self.keep_alive = False

	def connection_made(self, transport):
		if self.request is None:
			self.request = Request()

		self.transport = transport
		self.request.remote_addr = '{}:{}'.format(*transport.get_extra_info('peername'))

	def connection_lost(self, exc):
		pass

	def data_received(self, data):
		if self.request is None:
			self.request = Request()

		try:
			self.parse(data)
		except HTTPError as e:
			self.error(e)

	# noinspection PyProtectedMember
	def parse(self, data: bytes):
		req = self.request

		for line in BytesIO(data):
			if not req._f:
				req._f = True
				_ = _parse_first_line(line)
				if not _ or len(_) != 4:
					raise BadRequestError
				req.method, req.path, req.query_string, req.hv = _
				if self.vmap_case == '00':
					req.handler = self.router.find_handler(req)
					if not callable(req.handler):
						return self.finish()
			else:
				if req._body_length:
					req._body_lines.append(line)
					req._body_length += len(line)
					if req._body_length > req.content_length + 1:
						raise BadRequestError
					elif req._body_length == req.content_length + 1:
						return self.finish()
				else:
					if line == b'\r\n':
						if self.vmap_case == '10':
							req.handler = self.router.find_handler(req)
							if not callable(req.handler):
								return self.finish()

						if req.method in ['GET', 'HEAD']:
							return self.finish()

						if not req.content_length:
							raise LengthRequiredError()

						req._body_length = 1
						req._body_lines = []
					else:
						_parse_header_line(line, req)

	def finish(self):
		req = self.request
		delattr(req, '_f')
		delattr(req, '_body_length')

		self.request = None

		asyncio.get_event_loop().create_task(self.app.handle(req, self))

	def send(self, bs):
		self.transport.write(bs)

	def error(self, err, **kwargs):
		handler = self.app.error_handlers.get(err.status)
		if handler:
			return handler(err, **kwargs)
		else:
			return err.make_response(**kwargs)


class Response(object):
	__slots__ = (
		'time', 'status',
		'headers', 'cookie',
		'body', 'empty'
	)

	def __init__(self, status, headers=None, cookie=None, body=None, empty=False):
		self.time = -1

		self.status = status
		self.headers = headers or {}

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
				_b = str(self.body).encode('utf8', 'ignore')

			self.headers['Content-Length'] = len(self.body)

		_ = ['HTTP/1.0 {} {}'.format(self.status, reason)]
		if self.headers:
			_ += list(map(lambda item: '{}: {}'.format(*item), self.headers.items()))

		if self.cookie is not None:
			if self.cookie.a:
				_ += list(map(lambda x: 'Set-Cookie: {}'.format(x), self.cookie.a.values()))

			if self.cookie.r:
				_ += list(map(lambda x: 'Set-Cookie: {}'.format(x), self.cookie.r.values()))

		_ = list(map(lambda x: x.encode('latin1', 'ignore'), _))
		_.append(b'')
		if _b is not None:
			_.append(_b)

		return b'\r\n'.join(_)

	@classmethod
	def json(cls, status, data, cookie=None, ensure_ascii=False, dump_cls=None):
		return cls(
			status,
			cookie=cookie,
			body=json.dumps(data, ensure_ascii=ensure_ascii, cls=dump_cls),
			headers={'Content-Type': 'application/json'}
		)

	@classmethod
	def html(cls, status, html, cookie=None):
		return cls(status, body=html, cookie=cookie, headers={'Content-Type': 'text/html'})

	@classmethod
	def make_res(cls, res):
		if not isinstance(res, Response):
			status = 200
			body = res
			headers = None

			if isinstance(res, tuple):
				status, *others = res
				if len(others) == 2:
					body, headers = others

			res = Response(status, body=body, headers=headers)

		return res
