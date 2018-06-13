import asyncio
import json

from rain.ext.mysql.client import Mysql, Connection

from rain.ext.orm import field
from rain.ext.orm.components import Table
from rain.ext.orm.dml import InsertSQL, UpdateSQL

loop = asyncio.get_event_loop()

client = Mysql(**json.load(open('./config.json')).get('mysql'))

client.start()

conn: Connection = client.connections[0]


class User(Table):
	__auto_create__ = True

	id = field.INT(is_primary=True, auto_increment=True)
	name = field.CHAR(20, unique=True, index_key='name.unique')
	create_time = field.DATETIME()


insert = InsertSQL(User, prefix='IGNORE')

insert.values(
	lst=[
		{'name': b'spring', 'id': 34},
		{'name': '''f'"o'"o''', 'id': 45},
		{'name': b'''k"'"'ey''', 'id': 65},
		{'name': '''select * from user;''', 'id': 46}
	]
)

print(insert.render())

update = UpdateSQL(User)

update.values(name="select * from mysql.user where User='root'").where(User.id.op == 45)

print(update.render())
