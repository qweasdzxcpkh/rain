class MysqlError(Exception):
	pass


class OperationError(MysqlError):
	pass


class InternalError(MysqlError):
	pass
