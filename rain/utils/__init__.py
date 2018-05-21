from io import StringIO


class AttrDict(dict):
	def __getattr__(self, item):
		return self.get(item)

	def init(self, data):
		for k, v in data.items():
			if isinstance(v, dict) and not isinstance(v, AttrDict):
				self[k] = AttrDict().init(v)
			else:
				self[k] = v

		return self


class FakeTextFile(StringIO):
	def read(self):
		self.seek(0)
		return super().read()
