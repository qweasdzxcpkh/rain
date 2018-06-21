# 简介
杭州几乎每星期都会下雨，很烦，所以有了这个名字。

# 结构
>
    /rain
    |
    ---- app.py             class: <Rain>
    |
    ____ clses.py           class: <Request>, <Response>, <Cookie>
    |
    ____ error.py           class: <RainError>, ...
    |
    ____ form.py            class: <FormData>, <FormFile>, <HashFormFile>, <FileDatas>
    |
    ____ h2tp.py            class: <HTTPProtocol>
    |
    ---- router.py          class: <BaseRouter>   not use regexp
    |
    ---- tpl.py             class: <Tpl>  a simple html template engine, just like Jinja2.
    |
    ____ view.py            class: <BaseView> RESTful view class
    |
    ---- /ext
        |
        ---- /mysql         a simple async mysql client
        |
        ---- /redis         a simple async redis client

# Rain
>

    cd test && python main.py

# Mysql
>

    import asyncio
    
    from rain.ext.mysql import Mysql
    
    loop = asyncio.get_event_loop()
    
    client = Mysql(**conf)
    
    async def test():
        async with client.conn_ctx() as conn:
            result = await conn.query('select 12 +34 as sum')
    
            print(result.rows)
    
    loop.run_until_complete(test())
    
# Redis
>

    import asyncio

    from rain.ext.redis import Redis
    
    loop = asyncio.get_event_loop()
    
    r = Redis()
    r.start()
    
    async def redis_test():
        await r.mset('na""me', 'asdas asdas asdas')
        print(await r.mget('na""me'))
        print(await r.echo(b'asdasd'))
        print(await r.ping(cost_time=True))
    
    loop.run_until_complete(redis_test())
    
