# 简介

杭州几乎每星期都会下雨，很烦，所以有了这个名字。

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
        ---- /mysql         a simple async mysql client,[Doc](./mysql.md)
        |
        ---- /redis         a simple async redis client,[Doc](./redis.md)
    
