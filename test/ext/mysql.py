import asyncio
import json

from rain.ext.mysql.client import Mysql, Connection

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

client.start()

conn: Connection = client.connections[0]

print(
	loop.run_until_complete(
		conn.create_table('create table name (id integer primary key, name char(30) unique);')
	)
)
