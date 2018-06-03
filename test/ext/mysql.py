import asyncio
import json

from rain.ext.mysql.client import Mysql

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

client.start()

loop.run_forever()
