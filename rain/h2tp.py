import asyncio
from asyncio.streams import StreamReader

from rain.utils.funcwrap import cachedproperty
from rain.clses import Request
from rain.error import BadRequestError, UnsupportedMediaTypeError, LengthRequiredError, EntityTooLargeError

max_content_length = 3 * 1024 * 1024  # 3MB

request_content_types = {
	'text/xml',
	'text/plain',
	'text/json',
	'application/json',
	'application/x-www-form-urlencoded',
	'multipart/form-data'
}

support_methods = {'GET', 'POST', 'OPTIONS', 'HEAD', 'DELETE', 'PUT'}


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

	hv = hv.rstrip().split('/')[-1]

	return method.upper(), q, s, hv


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
			return UnsupportedMediaTypeError()
	elif k == 'content-length':
		if not v.isdigit() and req.method in {'PUT', 'POST', 'OPTIONS'}:
			return LengthRequiredError()
		v = int(v)
		if v > max_content_length:
			return EntityTooLargeError()

	req.headers[k] = v


class HTTPProtocol(asyncio.Protocol):
	request_cls = Request

	def __init__(self, app=None):
		self.app = app
		self.router = app.router
		self.transport = None
		self.reader = None
		self.writer = None
		self._request: Request = None
		self.keep_alive = False
		self.loop = asyncio.get_event_loop()

	@property
	def request(self):
		if self._request is None:
			self._request = self.request_cls()
			self._request.remote_addr = self.remoteaddr

		return self._request

	@cachedproperty
	def remoteaddr(self):
		return '{}:{}'.format(*self.transport.get_extra_info('peername'))

	def _del_req(self):
		self._request = None

	def connection_made(self, transport):
		self.reader = StreamReader(loop=self.loop)
		self.transport = transport

		self.request.remote_addr = self.remoteaddr
		self.reader.set_transport(transport)

		self.loop.create_task(self.parse())

	def data_received(self, data):
		self.reader.feed_data(data)

	# noinspection PyProtectedMember
	async def parse(self):
		while True:
			req = self.request
			line = await self.reader.readline()

			if not req._f:
				req._f = True
				_ = _parse_first_line(line)
				if not _ or len(_) != 4:
					req.parse_error = BadRequestError()
					return await self.finish()

				req.method, req.path, req.query_string, req.hv = _
			else:
				if req._body_length:
					req._body_lines.append(line)
					req._body_length += len(line)
					if req._body_length > req.content_length + 1:
						raise BadRequestError
					elif req._body_length == req.content_length + 1:
						return await self.finish()
				else:
					if line == b'\r\n':
						if req.method in {'GET', 'HEAD'} or not req.content_length:
							return await self.finish()

						req._body_length = 1
						req._body_lines = []
					else:
						error = _parse_header_line(line, req)
						if error is not None:
							req.parse_error = error
							return await self.finish()

	async def finish(self):
		req = self.request
		delattr(req, '_f')
		delattr(req, '_body_length')
		self._del_req()

		await self.app.handle(req, self)

		if req.keepalive:
			await self.parse()
		else:
			self.transport.close()

	def send(self, bs):
		self.transport.write(bs)

	def error(self, err, **kwargs):
		handler = self.app.error_handlers.get(err.status)
		if handler:
			return handler(err, **kwargs)
		else:
			return err.make_response(**kwargs)
