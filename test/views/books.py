from rain.view import BaseView


class Books(BaseView):
	def get(self, request):
		print(self.request)

		return 'Hello World~'


class BooksLst(BaseView):
	name = 'lst'

	def get(self, **kwargs):
		print(self.request)

		return 'BooksLst'
