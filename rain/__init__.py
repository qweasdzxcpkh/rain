from rain.app import Rain
from rain.ext.mysql import Mysql
from rain.ext.redis import Redis


class _G(object):
	_status = 0

	app: Rain = None
	debug: bool = False

	mysql: Mysql = None
	redis: Redis = None

	ext: dict = None

	def __getattribute__(self, item):
		if item == '__class__':
			return _G

		if item == 'lock':
			return super().__getattribute__(item)

		status = super().__getattribute__('_status')
		if status == 0:
			raise RuntimeError('G is not inited')

		return super().__getattribute__(item)

	def __setattr__(self, key, value):
		status = super().__getattribute__('_status')
		if status != 0:
			raise RuntimeError('G is locked')

		super().__setattr__(key, value)

	def lock(self):
		self.ext = {}
		super().__setattr__('_status', 1)


g = _G()

version = VERSION = '0.0.1'

ascii_logo = ASCII_LOGO = '''
 ██▀███   ▄▄▄       ██▓ ███▄    █ 
▓██ ▒ ██▒▒████▄    ▓██▒ ██ ▀█   █ 
▓██ ░▄█ ▒▒██  ▀█▄  ▒██▒▓██  ▀█ ██▒
▒██▀▀█▄  ░██▄▄▄▄██ ░██░▓██▒  ▐▌██▒
░██▓ ▒██▒ ▓█   ▓██▒░██░▒██░   ▓██░
░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░▓  ░ ▒░   ▒ ▒ 
  ░▒ ░ ▒░  ▒   ▒▒ ░ ▒ ░░ ░░   ░ ▒░
  ░░   ░   ░   ▒    ▒ ░   ░   ░ ░ 
   ░           ░  ░ ░           ░ 
'''.strip()  # http://patorjk.com/software/taag/#p=display&f=Bloody&t=Rain

desc = DESC = "A simple async http api server."

from rain.clses import Request, Response, Cookie
from rain.error import RainError, HTTPError
