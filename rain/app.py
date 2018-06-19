import os
import asyncio
from functools import partial
from inspect import isawaitable

from rain import ascii_logo
from rain.g import G
from rain.router import BaseRouter
from rain.clses import Response, Request
from rain.h2tp import HTTPProtocol
from rain.error import HTTPError, ServerError
from rain.utils.color import Color


class Rain(object):
	protocol_cls = HTTPProtocol
	response_cls = Response
	router_cls = BaseRouter
	request_cls = Request

	listen_all = False

	def __init__(
			self,
			name='Rain',
			view_paths=None,
			find_view_func=None,
			templates_path='./templates',
			debug=False,
			**kwargs
	):
		"""
		:param view_paths:
		:param find_view_func:

		you should set a find_view_func if you set many view_path.
		"""

		self.name = name
		self.debug = debug

		self.router = BaseRouter(
			view_paths,
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

		G.APP = self
		G.DEBUG = debug
		G.HOST = kwargs.get('host')
		G.PORT = kwargs.get('port')
		self.protocol_cls.request_cls = self.request_cls

		if G.HOST == '0.0.0.0' and not self.listen_all:
			raise ValueError('Rain is can not listen 0.0.0.0, please use Nginx.')

	def run(self, use_ascii_logo=True, show_router=False):
		if self.debug:
			self.loop.set_debug(True)

		for fn in self._before_start_funcs:
			_ = fn()

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
		res.req = request

		res.empty = empty
		if abs(res.status - 205) == 1:  # 204, 206
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
