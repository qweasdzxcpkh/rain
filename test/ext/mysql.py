import asyncio
import json

from rain.ext.mysql.constants import COMMAND
from rain.ext.mysql.client import Mysql, Connection

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

client.start()

conn: Connection = client.connections[0]

print(
	loop.run_until_complete(
		conn.execute_command(COMMAND.COM_QUERY, b'INSERT INTO User(id, name, create_time) VALUES (3, "nsdame", "2018-01-12 12:12:12")')
	).is_ok()
)
