from functools import wraps

_real_none = object()


class cachedproperty(property):
	def __init__(self, fget=None, fset=None, fdel=None, doc=None):
		super().__init__(
			fget=fget,
			fset=self._clean(fset),
			fdel=self._clean(fdel),
			doc=doc
		)
		self._cache = _real_none

	def _clean(self, fn):
		if fn is None:
			return

		@wraps(fn)
		def wrapper(*args, **kwargs):
			result = fn(*args, **kwargs)
			self._cache = _real_none
			return result

		return wrapper

	def __get__(self, ins, cls=None):
		if self._cache is _real_none:
			self._cache = self.fget(ins)

		return self._cache
