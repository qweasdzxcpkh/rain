import os
from io import BytesIO
from urllib.parse import unquote
import hashlib

_ln = tuple([None])
_l = tuple()


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

	def validate(self):
		pass

	def _setv(self, k, v):
		if isinstance(v, list):
			self[k] += v
		else:
			self[k].append(v)

	def update(self, m: dict, **kwargs):
		for k, v in m.items():
			if k in m:
				if isinstance(v, list):
					self[k] += v
				else:
					self[k].append(v)
			else:
				if isinstance(v, list):
					self[k] = v
				else:
					self[k] = [v]


class FormFile(BytesIO):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.form_name = ''
		self.file_name = ''

		self.headers = {}

		self.size = 0

		self.is_overflow = False
		self.__prev_line = None

		self._ok = False

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

		self._ok = True


class HashFormFile(FormFile):
	hash_method = hashlib.md5

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self._m = None

	@property
	def md5(self):
		if not self._ok:
			return ''

		if not isinstance(self._m, str):
			self._m = self._m.hexdigest()

		return self._m

	def _write(self, l):
		super()._write(l)

		if self._m is None:
			self._m = self.hash_method()

		self._m.update(l)


class FormFiles(FormData):
	pass
