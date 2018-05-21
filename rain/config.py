class Config(object):
	HOST = 'localhost'
	PORT = 8080
	DEBUG = False

	@classmethod
	def set(cls, name, val):
		setattr(cls, name.upper(), val)
