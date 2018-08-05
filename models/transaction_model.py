from io import BytesIO
from celery import Celery
from celery.utils.log import get_task_logger

import redis
import json
import proyecto.graham.settings
import pycurl
import util



from enum import IntEnum
from proyecto.graham.db import psql_db, BaseModel
#from genesis.db import psql_db, BaseModel
from peewee import *
import datetime
#from genesis import BaseModel
from user_model import *

#from graham.models.user_model import User

# Enum isn't a bad way to maintain transaction status in a single field
class TransactionStatus(IntEnum):
	PENDING = 1
	PROCESSED = 2
	FAILED = 3

# I'm thinking we don't need an entirely separate table for transaction type either, although this is more error-prone
class TransactionType(IntEnum):
	TIP = 1
	WITHDRAW = 2
	GIVEAWAY_QUEUED = 3
	GIVEAWAY_ACTIVE = 4

# I simplify some of the names here because I think it makes future code more clear.
# e.g.
# `Transaction.transaction_type_id` is a bit of a mouthful, `Transaction.type` is a bit easier to digest


"""
A model like this maps into a database table (in Postgres) that looks like this:

db_table = transactions
columns = id (primary key, index), source_user_id (foreign key with index), amount (decimal), target_user_id (foreign key with index), type (integer), .....

For our foreign keys they are stored as simply just an ID in the database, but in the ORM (peewee) object we can actually access the full model.

E.g:
Transaction.source_user.username

So that's why I rename them to get rid of the _id
"""

class Transaction(BaseModel):
	id = UUIDField(primary_key=True) # We'll use a custom UID here as the primary key, which will also serve as maintaining indempotency on transactions to the node
	source_user = ForeignKeyField(User(), backref='sent_transactions')
	amount = DecimalField(max_digits=20, decimal_places=6)
	target_user = ForeignKeyField(User, backref='received_transactions',null=True) # This may be NULL  because withdraws for example don't have a receiving user
	destination = CharField(null=True) # Destination ban_ or xrb_ address
	TransactionType = IntegerField()
	block_hash = CharField(null=True) # May be null if transaction failed or is pending
	status = IntegerField()
	created_at = DateTimeField(default=datetime.datetime.utcnow())
	
	logger = get_task_logger(__name__)

	r = redis.StrictRedis()
	app = Celery('graham', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
	app.conf.CELERY_MAX_CACHED_RESULTS = -1

	def communicate_wallet(wallet_command):
		buffer = BytesIO()
		c = pycurl.Curl()
		c.setopt(c.URL, settings.node_ip)
		c.setopt(c.PORT, settings.node_port)
		c.setopt(c.POSTFIELDS, json.dumps(wallet_command))
		c.setopt(c.WRITEFUNCTION, buffer.write)
		c.setopt(c.TIMEOUT, 300)
		c.perform()
		c.close()

		body = buffer.getvalue()
		parsed_json = json.loads(body.decode('iso-8859-1'))
		return parsed_json

	@app.task(bind=True, max_retries=10)
	def send_transaction(self, tx):
		"""creates a block and broadcasts it to the network, returns
		a dict if successful. Synchronization is 'loosely' enforced.
		There's not much point in running this function in parallel anyway,
		since the node processes them synchronously. The lock is just
		here to prevent a deadlock condition that has occured on the node"""
		with redis.Redis().lock(tx['source_address'], timeout=300):
			try:
				source_address = tx['source_address']
				to_address = tx['to_address']
				amount = tx['amount']
				uid = tx['uid']
				raw_withdraw_amt = int(amount) * util.RAW_PER_BAN if settings.banano else int(amount) * util.RAW_PER_RAI
				wallet_command = {
					'action': 'send',
					'wallet': settings.wallet,
					'source': source_address,
					'destination': to_address,
					'amount': raw_withdraw_amt,
					'id': uid
				}
				logger.debug("RPC Send")
				wallet_output = communicate_wallet(wallet_command)
				logger.debug("RPC Response")
				if 'block' in wallet_output:
					txid = wallet_output['block']
					# Also pocket these timely
					logger.info("Pocketing tip for %s, block %s", to_address, txid)
					pocket_tx(to_address, txid)
					ret = json.dumps({"success": {"source":source_address, "txid":txid, "uid":uid, "destination":to_address, "amount":amount}})
					r.rpush('/tx_completed', ret)
					return ret
				else:
					self.retry(countdown=2**self.request.retries)
					return {"status":"retrying"}
			except pycurl.error:
				self.retry(countdown=2**self.request.retries)
				return {"status":"retrying"}
			except Exception as e:
				logger.exception(e)
				self.retry(countdown=2**self.request.retries)
				return {"status":"retrying"}

	def pocket_tx(account, block):
		action = {
			"action":"receive",
			"wallet":settings.wallet,
			"account":account,
			"block":block
		}
		return communicate_wallet(action)

	@app.task
	def pocket_task(accounts):
		"""Poll pending transactions in accounts and pocket them"""
		processed_count = 0
		# The lock ensures we don't enter this function twice
		# It wouldn't hurt anything, but there's really no point to do so
		have_lock = False
		lock = redis.Redis().lock("POCKET_TASK", timeout=300)
		try:
			have_lock = lock.acquire(blocking=False)
			if not have_lock:
				logger.info("Could not acquire lock for POCKET_TASK")
				return None
			accts_pending_action = {
				"action":"accounts_pending",
				"accounts":accounts,
				"threshold":util.RAW_PER_BAN if settings.banano else util.RAW_PER_RAI,
				"count":5
			}
			resp = communicate_wallet(accts_pending_action)
			if resp is None or 'blocks' not in resp:
				return None
			for account, blocks in resp['blocks'].items():
				for b in blocks:
					logger.info("Receiving block %s for account %s", b, account)
					rcv_resp = pocket_tx(account, b)
					if rcv_resp is None or 'block' not in rcv_resp:
						logger.info("Couldn't receive %s - response: %s", b, str(rcv_resp))
					else:
						processed_count += 1
						logger.info("pocketed block %s", b)
			return processed_count
		except Exception as e:
			logger.exception(e)
			return None
		finally:
			if have_lock:
				lock.release()

	if __name__ == '__main__':
		#app.start()
		pass

	class Meta:
		db_table='transactions'








