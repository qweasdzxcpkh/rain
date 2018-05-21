from rain.view import BaseView
from rain.tpl import Tpl


class Home(BaseView):
	tpl_dir_path = r'C:\Users\ztk\Documents\rain\test\tpls'

	def get(self, **kwargs):
		self.request.cookie.add('name', 'spring', max_age=600)

		return self.render(
			'main.html',
			data=dict(
				name='Name',
				content='Hello World'
			)
		)

	def options(self, **kwargs):
		print(self.request.form)
		print(self.request.files)

		return 'OPTIONS'
