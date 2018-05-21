from rain.view import BaseView


class Home(BaseView):
	def get(self, **kwargs):
		return 'Hello World~'
