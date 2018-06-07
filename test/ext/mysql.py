import asyncio
import json

from rain.ext.mysql.client import Mysql, QueryResult, Connection

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

client.start()

result: QueryResult = loop.run_until_complete(client.query('select * from user', 1))

print(
	len(result.rows[0]) == len(result.fields)
)

print(
	result.rows[0].Host
)

conn: Connection = client.connections[0]

print(
	loop.run_until_complete(conn.create_db('spring'))
)
