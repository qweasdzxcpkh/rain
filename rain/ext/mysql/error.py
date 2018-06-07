class MysqlError(Exception):
	def __init__(self, error_no, msg):
		super().__init__(error_no, msg)

		self.error_no = error_no
		self.msg = msg
