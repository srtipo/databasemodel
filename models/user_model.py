from enum import IntEnum
#from genesis.db import BaseModel
from proyecto.graham.db import BaseModel
from peewee import *
import datetime

class UserRelationshipType(IntEnum):
    Favorites = 1
    Muted = 2


class User(BaseModel):
	id = BigIntegerField(primary_key=True)
	username = CharField(unique=True)
	created_at = DateTimeField(default=datetime.datetime.utcnow())

	class Meta:
		db_table = 'users' # This is the only place this is required, because `user` is a key word in postgres. But the other ones are for convenience

## We can also put some other things here, like UserFavorites


class UserRelationship(BaseModel):
    user_primary  = ForeignKeyField(User, backref='user_primary')
    user_secundary  = ForeignKeyField(User, backref='user_secundary')
    UserRelationshipType = IntegerField()
    created_at = DateTimeField(default=datetime.datetime.utcnow())
