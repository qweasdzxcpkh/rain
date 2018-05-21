from rain.view import BaseView


class Books(BaseView):
	def get(self, request, **kwargs):
		print(request)

		return 'Hello World~'


class BooksLst(BaseView):
	name = 'lst'

	def get(self, request, **kwargs):
		print(request)

		return 'BooksLst'
