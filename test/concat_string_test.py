import time
from functools import wraps


def run_count(count):
	def decorator(fn):
		@wraps(fn)
		def wrapper(*args, **kwargs):
			bt = time.time()

			for i in range(count):
				fn(*args, **kwargs)

			print('Run Func: {}, Cost: {}'.format(fn.__name__, time.time() - bt))

		return wrapper

	return decorator


test_decorator = run_count(10000000)

str1 = 'spring'
str2 = 'is'
str3 = 'the'
str4 = 'best'
str5 = 'season'


@test_decorator
def str_add(*args):
	_ = ''
	for s in args:
		_ += s

	return _


@test_decorator
def str_join(*args):
	return ''.join(args)


if __name__ == '__main__':
	str_add(str1, str2, str3, str4, str5)
	str_join(str1, str2, str3, str4, str5)

	'''
	Run Func: str_add, Cost: 3.190563678741455
	Run Func: str_join, Cost: 1.8223004341125488
	'''
