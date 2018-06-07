import re

_name_regexp = re.compile(r'^[_a-zA-Z][\w\d_]*$')


def name_check(name):
	return bool(_name_regexp.match(name))


if __name__ == '__main__':
	print(name_check('s_werQ的'))
	print(name_check('122Ui'))
