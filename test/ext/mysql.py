import asyncio
import json

from rain.ext.mysql.client import Mysql, QueryResult

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

client.start()

result: QueryResult = loop.run_until_complete(client.query('select * from user', 1))

print(
	len(result.rows[0]) == len(result.fields)
)

print(result.rows)

print(
	loop.run_until_complete(client.query('SELECT now() as now', 1)).fields[0].name
)

print(
	loop.run_until_complete(client.use('fwss'))
)

print(
	loop.run_until_complete(
		client.query('select * from account_user limit 10', 1)
	).rows
)

print(
	loop.run_until_complete(
		client.connections[0].ping()
	)
)

loop.run_forever()
