import asyncio
import json

from rain.ext.mysql.constants import COMMAND
from rain.ext.mysql.client import Mysql, Connection

from rain.ext.orm import field
from rain.ext.orm.components import Table
from rain.ext.orm.dml import InsertSQL

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

client.start()

conn: Connection = client.connections[0]


class User(Table):
	__auto_create__ = True

	id = field.INT(is_primary=True, auto_increment=True)
	name = field.CHAR(20, unique=True, index_key='name.unique')
	create_time = field.DATETIME()


insert = InsertSQL(User)

insert.values(
	lst=[
		{'name': b'spring', 'id': 34},
		{'name': '''f'"o'"o''', 'id': 45},
		{'name': b'''k"'"'ey''', 'id': 65}
	]
)

sql = insert.render()

print(sql)

print(
	loop.run_until_complete(
		conn.execute_command(COMMAND.COM_QUERY, sql)
	)
)
