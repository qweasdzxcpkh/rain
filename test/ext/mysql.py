import asyncio
import json

from rain.ext.mysql.client import Mysql, Connection

from rain.ext.orm import field
from rain.ext.orm.components import make_base
from rain.ext.orm.dml import InsertSQL, UpdateSQL

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

loop.run_until_complete(
	client.query('SELECT * from user;')
)
