import os
import asyncio
from functools import partial
from inspect import isawaitable

from rain import ascii_logo
from rain.config import Config
from rain.router import BaseRouter
from rain.clses import Response
from rain.h2tp import HTTPProtocol
from rain.error import HTTPError, ServerError
from rain.utils.color import Color


class Rain(object):
	protocol_cls = HTTPProtocol
	response_cls = Response
	router_cls = BaseRouter

	def __init__(
			self,
			name='Rain',
			view_paths=None,
			vmap_case='00',
			find_view_func=None,
			templates_path='./templates',
			debug=False,
			**kwargs
	):
		self.name = name
		self.debug = debug

		self.router = BaseRouter(
			view_paths,
			vmap_case=vmap_case,
			find_map_func=find_view_func
		)
		self.router.load()
		self.router.tpl_dir_path = os.path.abspath(templates_path)

		self._kwargs = kwargs
		self._server = None

		self.loop = asyncio.get_event_loop()

		self._before_start_funcs = []
		self._before_request_funcs = []
		self._after_request_funcs = []
		self.error_handlers = {}

		Config.DEBUG = debug
		Config.HOST = kwargs.get('host')
		Config.PORT = kwargs.get('port')

	def run(self, use_ascii_logo=True, show_router=False):
		if self.debug:
			self.loop.set_debug(True)

		for fn in self._before_start_funcs:
			fn()

		self._server = self.loop.run_until_complete(
			self.loop.create_server(
				partial(self.protocol_cls, app=self), **self._kwargs
			)
		)

		print(
			"""********************************************************************************
{} is running~

---- HOST: {}
---- PORT: {}
---- PID: {}
---- DEBUG: {}
{}
********************************************************************************
			""".format(
				Color(ascii_logo if use_ascii_logo else 'Rain').fg(Color.LCYAN),
				self._kwargs.get('host'),
				self._kwargs.get('port'),
				os.getpid(),
				self.debug,
				self.router.render() if show_router else ''
			).strip()
		)

		try:
			self.loop.run_forever()
		except KeyboardInterrupt:
			self.stop()

	def stop(self):
		if self._server is None:
			return

		self._server.close()
		self.loop.run_until_complete(self._server.wait_closed())
		self.loop.close()

	async def handle(self, request, protocol):
		empty = request.method == 'HEAD'
		handler = request.handler
		parse_error = request.parse_error

		if parse_error is None:
			# noinspection PyBroadException
			try:
				if handler is None:
					handler = self.router.find_handler(request, raise_error=True)

				for fn in self._before_request_funcs:
					r = fn(request)
					if isawaitable(r):
						await r

				res = handler()
				if isawaitable(res):
					res = await res

			except HTTPError as e:
				res = protocol.error(e)
			except Exception:
				res = ServerError().make_response()
		else:
			res = parse_error.make_response()

		res = self.response_cls.make_res(res)

		res.empty = empty
		if res.status in [204, 206]:
			res.empty = True

		res.cookie = request.cookie
		protocol.send(res.to_bytes())

		for fn in self._after_request_funcs:
			fn(request, res)

	def before_start(self, fn):
		self._before_start_funcs.append(fn)
		return fn

	def before_request(self, fn):
		self._before_request_funcs.append(fn)
		return fn

	def after_request(self, fn):
		self._after_request_funcs.append(fn)
		return fn

	def error_handler(self, error_code):
		def d(fn):
			self.error_handlers[error_code] = fn
			return fn

		return d
