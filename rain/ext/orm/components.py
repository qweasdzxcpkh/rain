from rain.ext.orm import field


class Table(object):
	__table__name__ = ''
	__auto_create__ = False


if __name__ == '__main__':
	class User(Table):
		id = field.INT(is_primary=True, auto_increment=True)
		name = field.CHAR(20, unique=True)
		create_time = field.DATETIME()


	print(User)
