import asyncio
import json

from rain.ext.mysql import Mysql

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))


async def test():
	async with client.conn_ctx() as conn:
		result = await conn.query('select 12 +34 as sum')

		print(result.rows)


loop.run_until_complete(test())
