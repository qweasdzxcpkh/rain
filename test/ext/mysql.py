import asyncio
import json

from rain.ext.mysql.client import Mysql, QueryResult

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

client.start()

result: QueryResult = loop.run_until_complete(client.query('select * from user', 1))

print(
	result.columns[0] == len(result.fields)
)

for col in result.columns:
	print(dict(zip(result.field_names, col)))

loop.run_forever()
