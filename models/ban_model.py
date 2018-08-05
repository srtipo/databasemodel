from enum import IntEnum

from peewee import *
from genesis.models.user_model import User

class BanType(IntEnum):
    STATS_BAN = 1
    FROZEN = 2
    TIP_BAN = 3

class Ban(BaseModel):
    user = ForeignKeyField(User, backref='bans')
    ban_type = IntegerField()
    created_at = DateTimeField(default=datetime.datetime.utcnow())

