import os
import sys

__project_path = os.path.dirname(os.getcwd())
if __project_path not in sys.path:
	sys.path.insert(0, __project_path)

from rain import Rain

app = Rain(
	view_paths=[
		{
			'path': './views',
			'name': 'default'
		}
	],
	port=8080,
	debug=True,
	# mysql_host='192.168.0.101',
	# mysql_database='mysql',
	# mysql_user='root',
	# mysql_password='112233',
	# redis_host='192.168.0.101',
	# redis_db=1
)


@app.before_request
def permission_check(req):
	# todo permission check
	pass


@app.after_request
def log(req, res):
	print('{} {} {:.5f}MS'.format(req, res, res.time - req.time))


if __name__ == '__main__':
	app.run(show_router=True)
