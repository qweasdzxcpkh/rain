import asyncio

from rain.view import BaseView


class Home(BaseView):
	async def get(self, **kwargs):
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

	async def post(self, **kwargs):
		await asyncio.sleep(0.5)

		self.request.file_hash_method = 'md5'  # set this, before form parse
		print(self.request.form)
		print(self.request.files.get('aaa').hash)

		return 'OK'
