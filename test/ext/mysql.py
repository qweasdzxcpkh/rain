import asyncio
import json

from rain.ext.orm import field
from rain.ext.orm.components import make_base
from rain.ext.orm.dml import InsertSQL

loop = asyncio.get_event_loop()

base = make_base(**json.load(open('./config.json')).get('mysql'))


class User(base.model):
	__auto_create__ = True
	__table_name__ = 'account_user'

	id = field.INT(is_primary=True, auto_increment=True)
	name = field.CHAR(20, unique=True)


class Group(base.model):
	__auto_create__ = True
	__table_name__ = 'account_group'

	id = field.INT(is_primary=True, auto_increment=True)
	name = field.CHAR(20, unique=True)


class GroupMember(base.model):
	__auto_create__ = True
	__table_name__ = 'account_group_member'

	gid = field.INT(is_primary=True)
	uid = field.INT(is_primary=True)


print(
	loop.run_until_complete(
		base.query(
			'''
			SELECT CONCAT(account_group.name, '.', account_user.name) as GU_NAME
			FROM account_user, account_group
			WHERE account_group.id = 4 AND account_user.id IN (
				SELECT account_group_member.uid
				FROM account_group_member
				WHERE account_group.id = 4
			)
			'''
		)
	).rows
)


async def insert():
	async with base.tran_ctx() as conn:
		await conn.execute(
			InsertSQL(User).values(
				[{'name': 'm'}, {'name': 'n'}]
			).render()
		)


loop.run_until_complete(insert())
