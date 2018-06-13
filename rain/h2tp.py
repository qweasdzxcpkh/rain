import asyncio
from asyncio.streams import StreamReader

from rain.clses import Request
from rain.error import BadRequestError, UnsupportedMediaTypeError, LengthRequiredError, EntityTooLargeError, \
	RequestTimeoutError, ResponseTimeoutError

max_request_wait_length = 15  # s

max_protocol_keep_alive_length = 15

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
			return UnsupportedMediaTypeError()
	elif k == 'content-length':
		if not v.isdigit() and req.method in {'PUT', 'POST', 'OPTIONS'}:
			return LengthRequiredError()
		v = int(v)
		if v > max_content_length:
			return EntityTooLargeError()

	req.headers[k] = v


class HTTPProtocol(asyncio.Protocol):
	def __init__(self, app=None):
		self.app = app
		self.router = app.router
		self.vmap_case = self.router.vmap_case
		self.transport = None
		self.reader = None
		self.writer = None
		self.request = None  # type: Request
		self.keep_alive = False
		self.loop = asyncio.get_event_loop()

	def connection_made(self, transport):
		self.request = Request()
		self.reader = StreamReader(loop=self.loop)
		self.transport = transport

		self.request.remote_addr = '{}:{}'.format(*transport.get_extra_info('peername'))
		self.reader.set_transport(transport)
		self.loop.create_task(self.parse())

	def connection_lost(self, exc):
		pass

	def data_received(self, data):
		if self.request is None:
			self.request = Request()

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
					return self.finish()

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

						if req.method in ['GET', 'HEAD'] or not req.content_length:
							return self.finish()

						req._body_length = 1
						req._body_lines = []
					else:
						error = _parse_header_line(line, req)
						if error is not None:
							req.parse_error = error
							return self.finish()

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
