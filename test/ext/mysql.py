import asyncio
import json

from rain.ext.mysql.client import Mysql
from rain.ext.mysql.constants import COMMAND

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

client.start()

print(
	loop.run_until_complete(
		client.execute_command(
			COMMAND.COM_PING,
			""
		)
	)
)

print(
	loop.run_until_complete(
		client.execute_command(
			COMMAND.COM_QUERY,
			"SELECT User FROM user;"
		)
	).read()
)

loop.run_forever()
