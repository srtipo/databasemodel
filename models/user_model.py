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

# To find user by id
def get_user_by_id(id):
    try:
        user = User.get(id==id)
        return user
    except User.DoesNotExist:
        logger.debug('user %s does not exist !')
        return None
def get_user_by_name(user_name):
    try:
        user = User.get(user_name=user_name)
        return user
    except User.DoesNotExist:
        logger.debug('user %s does not exist !')
        return None
def user_exists(id):
    return User.select().where(User.id == id).count() > 0
		
	
def get_user_by_wallet_address(address):
    try:
        user = Account.User.select().where(Account.User.wallet_address == address)
        return user
    except User.DoesNotExist:
        logger.debug('wallet %s does not exist !', address)
        return None
def get_by_id( id):
    try:
        user = User.select().where(User.id == id).get()
     except User.DoesNotExist:
        return None

def get_account(self):
    try:
        return self.account.get()
    except Account.DoesNotExist:
        return None

