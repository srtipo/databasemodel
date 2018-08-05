import datetime

from graham.db import psql_db, BaseModel
from peewee import *

from graham.models.user_model import User

class Giveaway(BaseModel):
	started_by = ForeignKeyField(User, backref='started_giveaways')
	giveway_amount = DecimalField(max_digits=20, decimal_places=6)
	tip_amount = DecimalField(max_digits=20, decimal_places=6)
	end_time = DateTimeField(null=True, default=None)
	channel_id = BigIntegerField() 
	winner_user_id = ForeignKeyField(User, backref='won_giveaways_winner_user_id', null=True)
	entry_fee = DecimalField(max_digits=20, decimal_places=6)



class Contestant(BaseModel):
	giveaway_id = ForeignKeyField(Giveaway, backref='contestants')
	user = ForeignKeyField(User, backref='entered_giveaways')
	created_at = DateTimeField(default=datetime.datetime.utcnow())
