def escape_string(txt):
	if '"' in txt:
		_ = "'{}'"
	else:
		_ = '"{}"'

	return _.format(txt)
