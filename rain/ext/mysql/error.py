_ = int.from_bytes(b'#', 'little')


class MysqlError(Exception):
	def __init__(self, error_no, msg):
		if msg[0] == _:
			msg = msg[6:]

		msg = msg.decode()
		super().__init__(error_no, msg)

		self.error_no = error_no
		self.msg = msg
