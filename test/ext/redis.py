import asyncio

from rain.ext.redis.client import Redis

loop = asyncio.get_event_loop()
loop.set_debug(True)

r = Redis()
r.start()


async def redis_test():
	await r.mset('na""me', 'asdas asdas asdas')
	print(await r.mget('na""me'))


loop.run_until_complete(redis_test())
