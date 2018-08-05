#from graham.db import BaseModel, psql_db
from proyecto.graham.db import BaseModel, psql_db
from peewee import *
import datetime
#from graham.models.user_model import User
from proyecto.graham.models.user_model import User
import util
import datetime
import proyecto.graham.settings
import asyncio
import aiohttp
import socket

class Account(BaseModel):
	user = ForeignKeyField(User, backref='account',unique=True)
	address = CharField(unique=True)
	pending_receive = DecimalField(default=0)
	pending_send = DecimalField(default=0)
	created_at = DateTimeField(default=datetime.datetime.utcnow())



