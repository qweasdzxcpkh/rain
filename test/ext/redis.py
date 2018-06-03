import asyncio
import json

from rain.ext.redis.client import Redis

loop = asyncio.get_event_loop()
loop.set_debug(True)

r = Redis(**json.load(open('./config.json')).get('redis'))
r.start()

print(loop.run_until_complete(r.mget('name', 'price')))

loop.run_forever()
