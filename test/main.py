from rain import Rain

app = Rain(
	host='localhost',
	view_paths=[
		{
			'path': './views',
			'name': 'default'
		}
	],
	vmap_case='',
	port=8080,
	debug=True
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
