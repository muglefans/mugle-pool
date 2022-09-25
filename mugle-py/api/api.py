#!/usr/bin/python3

# Copyright 2018 Blade M. Doyle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import json
import time
import redis
from datetime import datetime
import requests



from flask import Flask, request, jsonify, url_for, g, send_from_directory
from flask_login import login_required, LoginManager
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from muglebase.model.mugle_stats import Mugle_stats
from muglebase.model.blocks import Blocks
from muglebase.model.pool_stats import Pool_stats
from muglebase.model.pool_blocks import Pool_blocks
from muglebase.model.worker_stats import Worker_stats
from muglebase.model.worker_shares import Worker_shares
from muglebase.model.gps import Gps
from muglebase.model.shares import Shares
from muglebase.model.pool_utxo import Pool_utxo
from muglebase.model.pool_payment import Pool_payment
from muglebase.model.users import Users

from muglelib import lib
from muglelib import mugle
from muglelib import pool

# so hard...
#import pprint
#pp = pprint.PrettyPrinter(indent=4)

PROCESS = "poolapi"

# Check if debug message printing is requested
debug = lib.get_debug()

# From K8s secret
admin_user = os.environ["MUGLE_POOL_ADMIN_USER"]
admin_pass = os.environ["MUGLE_POOL_ADMIN_PASSWORD"]
app_secret_key = "xxxxyyyyyzzzzz" # os.environ["APP_SECRET_KEY"]

# Admin user is created as id=1 in dbinit
ADMIN_ID = 1

# Move these limits to config
mugle_blocks_range_limit = 501
mugle_stats_range_limit = 240
pool_blocks_range_limit = 5001
pool_stats_range_limit = 240
worker_stats_range_limit = 240
worker_shares_range_limit = 240
worker_block_range_limit = 240
worker_payment_record_range_limit = 240
redis_userid_key = "userid."

##
# App
app = Flask(__name__)
cache = Cache( 
    app,
    config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_HOST': 'redis-master',
        'CACHE_REDIS_PORT': 6379,
        # 'CACHE_REDIS_PASSWORD': app_secret_key,
    }
)
app.secret_key = app_secret_key
# CORS XXX REMOVE before mainnet
CORS(app)
# basicauth
login_manager = LoginManager()
login_manager.init_app(app)
auth = HTTPBasicAuth()
# Rate Limiting
limiter = Limiter(app, key_func=get_remote_address)
# The API
api = Api(app)
# The database handle
database = lib.get_db()
LOGGER = lib.get_logger(PROCESS)

r = redis.Redis(
    host='redis-master',
    port=6379)


@app.before_request
def pre_request():
    global database
    database.db.initializeSession()
    g.start = time.time()

@app.after_request
def after_request(response):
    global LOGGER
    timediff = time.time() - g.start
    debug and LOGGER.warn("Exec time: {}".format(str(timediff)))
    return response

@app.teardown_request
def teardn_request(response):
    global database
    database.db.destroySession()
    return response

class test(Resource):
    @auth.login_required
    def get(self):
        response = jsonify({ 'data': 'Hello, {}! Your user id is {}'.format(g.user.username, g.user.id) })
        response.status_code = 200
        return response

# ------------------
# Filter object fields
def filterby(obj, fields):
    if fields != None:
        for k in list(obj.keys()):
            if k not in fields:
                del obj[k]
    return obj
# ------------------


# ------------------

##
# Auth

# Given username or taken, and optionally a password, verify they match
@auth.verify_password
def verify_password(username_or_token, password=None):
    global database
    #database = lib.get_db()
    LOGGER = lib.get_logger(PROCESS)
    debug and LOGGER.warn("Will Verify User: {}, {}".format(username_or_token, password))
    # First try to verify via token
    user_rec = Users.verify_auth_token(app.config['SECRET_KEY'], username_or_token)
    if user_rec is None:
        # try to authenticate with username/password
        user_rec = Users.get(username_or_token, password)
    if user_rec is None:
        return False
    g.user = user_rec
    # Cache username<->user_id in redis for our stratum server
    redis_key = redis_userid_key + user_rec.username
    r.set(redis_key, user_rec.id)
    redis_key = redis_userid_key + user_rec.username.lower()
    r.set(redis_key, user_rec.id)
    return True

# XXX TODO:
# def change_password(username_or_token, new_password, password=None):
#     xxx TODO


#################
# -- Pool User Accounts

class PoolAPI_users(Resource):
    def post(self):
        global database
        LOGGER = lib.get_logger(PROCESS)
        username = None
        password = None
        try:
            debug and print("json request = {}".format(request.form))
            username = request.form.get('username')
            password = request.form.get('password')
            debug and LOGGER.warn("PoolAPI_users POST: user:{} password:{}".format(username, password))
        except AttributeError as e:
            LOGGER.warn("Missing username or password - {}".format(str(e)))
        if username is None or password is None:
            response = jsonify({ 'message': 'Missing arguments: username and pasword required' })
            response.status_code = 400
            return response
        if username == "" or password == "":
            response = jsonify({ 'message': 'Missing arguments: username and pasword required' })
            response.status_code = 400
            return response
        if "." in username:
            response = jsonify({ 'message': 'Invalid Username: May not contain "."' })
            response.status_code = 400
            return response
        # Check if the username is taken
        exists = Users.check_username_exists(username)
        if exists:
            debug and print("Failed to add - conflict with existing user = {}".format(username))
            response = jsonify({ 'message': 'Conflict with existing account' })
            response.status_code = 409
            return response
        # Create the users record
        user_rec = Users.create(username, password)
        if user_rec is None:
            debug and print("Failed to add - unable to create a new user record")
            response = jsonify({ 'message': 'System Error: Failed to create account' })
            response.status_code = 500
            return response
        # initialize a worker_stats record for this user (previous block) so they get instance feedback on the UI
        lb = Blocks.get_latest()
        if lb is not None:
            height = Blocks.get_latest().height
            initial_stat = Worker_stats(datetime.utcnow(), height, user_rec.id)
            database.db.createDataObj(initial_stat)
        # Cache username<->user_id in redis for our stratum server
        redis_key = redis_userid_key + user_rec.username
        r.set(redis_key, user_rec.id)
        debug and print("Added user = {}".format(user_rec))
        response = jsonify({ 'username': user_rec.username, 'id': user_rec.id })
        response.status_code = 201
        return response

    #decorators = [limiter.limit("5/minute"), auth.login_required]
    @auth.login_required
    def get(self, fields=None):
        if fields == None:
            # Get a login token
            token = g.user.generate_auth_token(app.config['SECRET_KEY'], expiration=86400)
            response = jsonify({ 'token': token.decode('ascii'), 'id': g.user.id })
            response.status_code = 200
            return response
        else:
            # Get user data
            return g.user.to_json(fields)

api.add_resource(PoolAPI_users,
        '/pool/users',     # GET:  Get a login token
                           # POST: Create a new user account
        '/pool/users/<string:fields>',   # Get data on single user
)


##
# Get a user ID
class PoolAPI_userid(Resource):
    @cache.cached(timeout=100)
    def get(self, username):
        try:
            userid = Users.get_id_by_username(username)
            if userid is None:
                response = jsonify({ 'id': None })
                response.status_code = 404
                return response
            response = jsonify({ 'id': userid })
            response.status_code = 200
            return response
        except Exception as e:
            LOGGER = lib.get_logger(PROCESS)
            LOGGER.error("Failed to lookup user: {} because: {}".format(username, repr(e)))
            response = jsonify({ 'message': 'Failed to lookup user: {}'.format(username) })
            response.status_code = 500
            return response

api.add_resource(PoolAPI_userid,
        '/pool/userid/<string:username>',     # GET:  Get userID by username
)

#################
# -- Mugle Network

##
# Stats
class MugleAPI_stats(Resource):
    #decorators = [limiter.limit("50/minute")]
    @cache.cached(timeout=10)
    def get(self, height=None, range=None, fields=None):
        LOGGER = lib.get_logger(PROCESS)
        debug and LOGGER.warn("MugleAPI_stats get height:{} range:{} fields:{}".format(height, range, fields))
        # Enforce range limit
        if range is not None:
            range = min(range, mugle_stats_range_limit)
        fields = lib.fields_to_list(fields)
        if height is None or height == 0:
            stats = Mugle_stats.get_latest(range)
        else:
            stats = Mugle_stats.get_by_height(height, range)
        #pp.pprint(stats)
        
        if range == None:
            if stats is None:
                return None
            return stats.to_json(fields)
        else:
            st = []
            for stat in stats:
                st.append(stat.to_json(fields))
            return st

api.add_resource(MugleAPI_stats,
        '/mugle/stat',
        '/mugle/stat/<string:fields>',
        '/mugle/stat/<int:height>',
        '/mugle/stat/<int:height>/<string:fields>',
        '/mugle/stats/<int:height>,<int:range>',
        '/mugle/stats/<int:height>,<int:range>/<string:fields>',
)

##
# Blocks
class MugleAPI_blocks(Resource):
    #decorators = [limiter.limit("50/minute")]
    @cache.cached(timeout=10)
    def get(self, height=None, range=None, fields=None):
        LOGGER = lib.get_logger(PROCESS)
        debug and LOGGER.warn("MugleAPI_blocks get height:{} range:{} fields:{}".format(height, range, fields))
        # Enforce range limit
        if range is not None:
            range = min(range, mugle_blocks_range_limit)
        fields = lib.fields_to_list(fields)
        if height is None or height == 0:
            blocks = Blocks.get_latest(range)
        else:
            blocks = Blocks.get_by_height(height, range)
        if range == None:
            if blocks is None:
                return None
            return blocks.to_json(fields)
        else:
            bl = []
            for block in blocks:
                bl.append(block.to_json(fields))
            return bl

api.add_resource(MugleAPI_blocks,
        '/mugle/block',
        '/mugle/block/<string:fields>',
        '/mugle/block/<int:height>',
        '/mugle/block/<int:height>/<string:fields>',
        '/mugle/blocks/<int:height>,<int:range>',
        '/mugle/blocks/<int:height>,<int:range>/<string:fields>')



#########
# -- Pool

##
# Blocks
class PoolAPI_blocks(Resource):
    #decorators = [limiter.limit("50/minute")]
    @cache.cached(timeout=10)
    def get(self, height=None, range=None, fields=None):
        LOGGER = lib.get_logger(PROCESS)
        debug and LOGGER.warn("PoolAPI_blocks get height:{}, range:{}, fields:{}".format(height, range, fields))
        # Enforce range limit
        if range is not None:
            range = min(range, pool_blocks_range_limit)
        fields = lib.fields_to_list(fields)
        if height is None or height == 0:
            blocks = Pool_blocks.get_latest(range)
        else:
            blocks = Pool_blocks.get_by_height(height, range)
        if range == None:
            if blocks is None:
                return None
            return blocks.to_json(fields)
        else:
            bl = []
            for block in blocks:
                bl = [block.to_json(fields)] + bl
            return bl

api.add_resource(PoolAPI_blocks,
        '/pool/block',
        '/pool/block/<string:fields>',
        '/pool/block/<int:height>',
        '/pool/block/<int:height>/<string:fields>',
        '/pool/blocks/<int:height>,<int:range>',
        '/pool/blocks/<int:height>,<int:range>/<string:fields>',
)

class PoolAPI_blocksCount(Resource):
    #decorators = [limiter.limit("50/minute")]
    @cache.cached(timeout=10)
    def get(self, height=None):
        LOGGER = lib.get_logger(PROCESS)
        debug and LOGGER.warn("PoolAPI_blocksCount get height:{}".format(height))
        count = Pool_blocks.count(height)
        return count

api.add_resource(PoolAPI_blocksCount,
        '/pool/blocks/count',
        '/pool/blocks/count/<int:height>',
)


##
# Stats
class PoolAPI_stats(Resource):
    #decorators = [limiter.limit("50/minute")]
    @cache.cached(timeout=10)
    def get(self, height=None, range=None, fields=None):
        LOGGER = lib.get_logger(PROCESS)
        debug and LOGGER.warn("PoolAPI_stats get height:{} range:{} fields:{}".format(height, range, fields))
        # Enforce range limit
        if range is not None:
            range = min(range, pool_stats_range_limit)
        fields = lib.fields_to_list(fields)
        if height is None or height == 0:
            stats = Pool_stats.get_latest(range)
        else:
            stats = Pool_stats.get_by_height(height, range)
        if range == None:
            if stats is None:
                return None
            return stats.to_json(fields)
        else:
            st = []
            for stat in stats:
                st.append(stat.to_json(fields))
            return st

api.add_resource(PoolAPI_stats,
        '/pool/stat',
        '/pool/stat/<string:fields>',
        '/pool/stat/<int:height>',
        '/pool/stat/<int:height>/<string:fields>',
        '/pool/stats/<int:height>,<int:range>',
        '/pool/stats/<int:height>,<int:range>/<string:fields>')


##
# Shares
class PoolAPI_shareCount(Resource):
    #decorators = [limiter.limit("50/minute")]
    @cache.cached(timeout=10)
    def get(self, height=None, range=None):
        global database
        #database = lib.get_db()
        LOGGER = lib.get_logger(PROCESS)
        debug and LOGGER.warn("PoolAPI_shareCount get height:{} range:{}".format(height, range))
        # Totals across all workers are stored in the Pool_stats record
        if range is None:
            if height is None:
                height = 0
            pool_st_rec = Pool_stats.get_by_height(height)
            if pool_st_rec is None:
                total = 0
                this_block = 0
            else:
                total = pool_st_rec.total_shares_processed
                this_block = pool_st_rec.shares_processed
            return  { "height": pool_st_rec.height,
                       "total": total,
                       "count": this_block,
                     }
        else:
            counts = []
            pool_st_recs = Pool_stats.get_by_height(height, range)
            for st_rec in pool_st_recs:
                rec = { "height": st_rec.height,
                        "total": st_rec.total_shares_processed,
                        "count": st_rec.shares_processed,
                      }
                counts.append(rec)
            return counts

api.add_resource(PoolAPI_shareCount,                                                              
        '/pool/share/count',                                                                      
        '/pool/share/count/<int:height>',
        '/pool/share/counts/<int:height>,<int:range>',
)


######################
# -- Mugle-Pool Workers

##
# Stats

# For All active Workers
class WorkersAPI_stats(Resource):
    #decorators = [limiter.limit("50/minute"), auth.login_required]
    @cache.cached(timeout=5)
    @auth.login_required
    def get(self, height=0, range=None, fields=None):
        global database
        #database = lib.get_db()
        LOGGER = lib.get_logger(PROCESS)
        debug and LOGGER.warn("WorkersAPI_stats get height:{} range:{} fields:{}".format(height, range, fields))
        fields = lib.fields_to_list(fields)
        stats = []
        if height == 0:
            height = Blocks.get_latest().height
        for stat in Worker_stats.get_by_height(height, range):
            # AUTH FILTER
            if stat.user_id == ADMIN_ID:
                stats.append(stat.to_json(fields))

        return stats

# All active workers
api.add_resource(WorkersAPI_stats,
        '/workers/stat',
        '/workers/stat/<string:fields>',
        '/workers/stat/<int:height>',
        '/workers/stat/<int:height>/<string:fields>',
        '/workers/stats/<int:height>,<int:range>',
        '/workers/stats/<int:height>,<int:range>/<string:fields>'
)


# For one specific worker
class WorkerAPI_stats(Resource):
    #decorators = [limiter.limit("50/minute"), auth.login_required]
    @cache.cached(timeout=5)
    @auth.login_required
    def get(self, id, height=0, range=None, fields=None):
        global database
        #database = lib.get_db()
        LOGGER = lib.get_logger(PROCESS)
        # AUTH FILTER
        if id != g.user.id:
            response = jsonify({ 'message': 'Not authorized to access data for other users' })
            response.status_code = 403
            return response
        debug and LOGGER.warn("WorkerAPI_stats get id:{} height:{} range:{} fields:{}".format(id, height, range, fields))
        # Enforce range limit
        if range is not None:
            range = min(range, worker_stats_range_limit)
        fields = lib.fields_to_list(fields)
        res = None
        if range is None:
            # Getting a single record
            if height == 0:
                # Get the most recent stats for this user
                res = Worker_stats.get_latest_by_id(id)
            else:
                res = Worker_stats.get_by_height_and_id(id, height)
            if res is None:
                return None
            return res.to_json(fields)
        else:
            # Getting a range of records
            if height == 0:
                height = Blocks.get_latest().height
            res = Worker_stats.get_by_height_and_id(id, height, range)
            if res is None:
                return None
            stats = []
            for stat in res:
                stats.append(stat.to_json(fields))
            return stats

api.add_resource(WorkerAPI_stats,
        # One specific worker
        '/worker/stat/<int:id>',
        '/worker/stat/<int:id>/<string:fields>',
        '/worker/stat/<int:id>/<int:height>',
        '/worker/stat/<int:id>/<int:height>/<string:fields>',
        '/worker/stats/<int:id>/<int:height>,<int:range>',
        '/worker/stats/<int:id>/<int:height>,<int:range>/<string:fields>'
)


# For All active Workers
class WorkersAPI_shares(Resource):
    #decorators = [limiter.limit("50/minute"), auth.login_required]
    @cache.cached(timeout=5)
    @auth.login_required
    def get(self, height=0, range=None, fields=None):
        global database
        #database = lib.get_db()
        LOGGER = lib.get_logger(PROCESS)
        debug and LOGGER.warn("WorkersAPI_shares get height:{} range:{} fields:{}".format(height, range, fields))
        fields = lib.fields_to_list(fields)
        shares_records = []
        if height == 0:
            height = Blocks.get_latest().height
        for shares in Worker_shares.get_by_height(height, range):
            # AUTH FILTER
            if shares.user_id == g.user.id:
                shares_records.append(shares.to_json(fields))
        return shares_records

api.add_resource(WorkersAPI_shares,
        # All active workers
        '/workers/shares',
        '/workers/shares/<string:fields>',
        '/workers/shares/<int:height>',
        '/workers/shares/<int:height>/<string:fields>',
        '/workers/shares/<int:height>,<int:range>',
        '/workers/shares/<int:height>,<int:range>/<string:fields>'
)
 

# For one specific active Worker
class WorkerAPI_shares(Resource):
    #decorators = [limiter.limit("50/minute"), auth.login_required]
    @cache.cached(timeout=5)
    @auth.login_required
    def get(self, id=None, height=None, range=0, fields=None):
        global database
        #database = lib.get_db()
        LOGGER = lib.get_logger(PROCESS)
        # AUTH FILTER
        if id != g.user.id:
            response = jsonify({ 'message': 'Not authorized to access data for other users' })
            response.status_code = 403
            return response
        debug and LOGGER.warn("WorkerAPI_shares get id:{} height:{} range:{} fields:{}".format(id, height, range, fields))
        # Enforce range limit
        if range is not None:
            range = min(range, worker_shares_range_limit)
        fields = lib.fields_to_list(fields)
        if height is None:
            return Worker_shares.get_latest_height(id)
        if height == 0:
            height = Blocks.get_latest().height
        shares_records = []
        if id is None:
            for shares in Worker_shares.get_by_height(height, range):
                shares_records.append(shares.to_json(fields))
            return shares_records
        else:
            if range is None:
                worker_sh_recs = Worker_shares.get_by_height_and_id(height, id)
                #print("worker_sh_recs = {}".format(worker_sh_recs))
                if res is None:
                    return "[]".to_json()
                return res.to_json(fields)
            else:
                for share in Worker_shares.get_by_height_and_id(height, id, range):
                    shares_records.append(share.to_json(fields))
                return shares_records

api.add_resource(WorkerAPI_shares,
        # One specific worker
        '/worker/shares/<int:id>',
        '/worker/shares/<int:id>/<string:fields>',
        '/worker/shares/<int:id>/<int:height>',
        '/worker/shares/<int:id>/<int:height>/<string:fields>',
        '/worker/shares/<int:id>/<int:height>,<int:range>',
        '/worker/shares/<int:id>/<int:height>,<int:range>/<string:fields>')


class WorkerAPI_blocks(Resource):
    #decorators = [limiter.limit("50/minute"), auth.login_required]
    @cache.cached(timeout=5)
    @auth.login_required
    def get(self, id, height=None, range=None, fields=None):
        global database
        #database = lib.get_db()
        # Enforce range limit
        if range is not None:
            range = min(range, worker_block_range_limit)
        fields = lib.fields_to_list(fields)
        # AUTH FILTER
        if id != g.user.id:
            response = jsonify({ 'message': 'Not authorized to access data for other users' })
            response.status_code = 403
            return response
        if height is None or height == 0:
            blocks = Pool_blocks.get_latest(range, id)
        else:
            blocks = Pool_blocks.get_by_height(height, range, id)
        if range == None:
            if blocks is None:
                return None
            return blocks.to_json(fields, True)
        else:
            bl = []
            for block in blocks:
                bl.append(block.to_json(fields, True))
            return bl

api.add_resource(WorkerAPI_blocks,
        '/worker/block/<int:id>',
        '/worker/block/<int:id>/<string:fields>',
        '/worker/block/<int:id>/<int:height>',
        '/worker/block/<int:id>/<int:height>/<string:fields>',
        '/worker/block/<int:id>/<int:height>,<int:range>',
        '/worker/block/<int:id>/<int:height>,<int:range>/<string:fields>',
)


######################
# -- Worker Balance and Payments

##
# pool_utxo
class WorkerAPI_utxo(Resource):
    #decorators = [limiter.limit("50/minute"), auth.login_required]
    @auth.login_required
    def get(self, id, fields=None):
        global database
        #database = lib.get_db()
        LOGGER = lib.get_logger(PROCESS)
        # AUTH FILTER
        if id != g.user.id:
            response = jsonify({ 'message': 'Not authorized to access data for other users' })
            response.status_code = 403
            return response
        debug and LOGGER.warn("WorkerAPI_utxo get id:{} fields:{}".format(id, fields))
        fields = lib.fields_to_list(fields)
        utxo = Pool_utxo.get_by_userid(id)
        if utxo is None:
            return None
        return utxo.to_json(fields)

    #decorators = [limiter.limit("50/minute"), auth.login_required]
    @auth.login_required
    def post(self, id, field, value):
        global database
        #database = lib.get_db()
        LOGGER = lib.get_logger(PROCESS)
        # AUTH FILTER
        if id != g.user.id:
            response = jsonify({ 'message': 'Not authorized to access data for other users' })
            response.status_code = 403
            return response
        debug and LOGGER.warn("WorkerAPI_utxo post id:{} field:{} value:{}".format(id, field, value))
        allowed_fields = ["address", "method"]
        if field not in allowed_fields:
            response = jsonify({ 'message': 'Invalid field for update' })
            response.status_code = 403
            return response
        st = False
        if field == "address":
            st = Pool_utxo.update_address(id, value)
        elif field == "method":
            st = Pool_utxo.update_method(id, value)
        if st == False:
            response = jsonify({ 'message': 'Failed to update {}'.format(field) })
            response.status_code = 500
            return response
        else:
            response = jsonify({ field: value })
            response.status_code = 200
            return response

api.add_resource(WorkerAPI_utxo,
        '/worker/utxo/<int:id>',
        '/worker/utxo/<int:id>/<string:field>/<string:value>', # POST
)

##
# pool_payments
class WorkerAPI_payments(Resource):
    #decorators = [limiter.limit("50/minute"), auth.login_required]
    @auth.login_required
    def get(self, id, range=None, fields=None):
        global database
        #database = lib.get_db()
        LOGGER = lib.get_logger(PROCESS)
        # AUTH FILTER
        if id != g.user.id:
            response = jsonify({ 'message': 'Not authorized to access data for other users' })
            response.status_code = 403
            return response
        debug and LOGGER.warn("WorkerAPI_payments get id:{} range:{} fields:{}".format(id, range, fields))
        # Enforce range limit
        if range is not None:
            range = min(range, worker_payment_record_range_limit)
        fields = lib.fields_to_list(fields)
        if range is None:
            payment_rec = Pool_payment.get_latest_by_userid(id)
            if payment_rec is None:
                return None
            return payment_rec.to_json(fields)
        else:
            payments = []
            for payment_rec in Pool_payment.get_latest_by_userid(id, range):
                payments.append(payment_rec.to_json(fields))
            return payments

api.add_resource(WorkerAPI_payments,
        '/worker/payment/<int:id>',
        '/worker/payment/<int:id>/<string:fields>',
        '/worker/payments/<int:id>/<int:range>',
        '/worker/payments/<int:id>/<int:range>/<string:fields>'
)

##
# Estimations
# height = None: Get immature balance estimate
# height = "next": Get estimate for "next block found"
# height = #: Get estimate for pool block at height #
# range  = #: Get estimate for range of pool blocks around height #
class EstimateApi_payment(Resource):
    decorators = [auth.login_required, cache.cached(timeout=300)]
    #@auth.login_required
    def get(self, id, height=None, range=None):
        LOGGER = lib.get_logger(PROCESS)
        if id != g.user.id:
            response = jsonify({ 'message': 'Not authorized to access data for other users' })
            response.status_code = 403
            return response
        debug and LOGGER.warn("EstimateApi_payment get id:{} height:{}".format(id, height))
        id_str = str(id)
        if height is None:
            # Immature Balance Estimate
            LOGGER.warn("Immature Balance Estimate")
            # Get a list of all new and unlocked blocks
            unlocked_blocks = Pool_blocks.get_all_unlocked()
            unlocked_blocks_h = [blk.height for blk in unlocked_blocks]
            #LOGGER.warn("EstimateApi_payment unlocked blocks: {}".format(unlocked_blocks))
            new_blocks = Pool_blocks.get_all_new()
            new_blocks_h = [blk.height for blk in new_blocks]
            #LOGGER.warn("EstimateApi_payment new blocks: {}".format(new_blocks))
            total = 0
            for height in unlocked_blocks_h + new_blocks_h:
                debug and print("Estimate block at height: {}".format(height))
                payout_map = pool.get_block_payout_map_estimate(height, LOGGER)
                if payout_map is not None and id_str in payout_map:
                    total = total + payout_map[id_str]
            return {"immature": total}
        if type(height) == str:
            if height == "next":
                # Next block estimate
                debug and LOGGER.warn("Next block estimate")
                estimate = 0
                payout_map = pool.get_block_payout_map_estimate(height, LOGGER)
                if payout_map is None:
                    estimate = "TBD"
                elif id_str in payout_map:
                    estimate = payout_map[id_str]
                else:
                    estimate = 0
                return {"next": estimate}
            else:
                response = jsonify({ 'message': 'Invalid Request' })
                response.status_code = 400
                return response
        # Block Reward estimate
        if range is None:
            # One specific block estimate
            debug and LOGGER.warn("One specific block estimate")
            estimate = 0
            payout_map = pool.get_block_payout_map_estimate(height, LOGGER)
            if payout_map is not None:
                if id_str in payout_map.keys():
                   estimate = payout_map[id_str]
                else:
                   estimate = 0
            else:
                # Maybe this is a pool block but we didnt estimate it yet
                pb = Pool_blocks.get_by_height(height)
                if pb is not None:
                    estimate = "TBD"
            str_height = str(height)
            return {str_height: estimate}
        # Range of pool block reward estimates
        debug and LOGGER.warn("Range of blocks estimate")
        # Enforce range limit
        range = min(range, pool_blocks_range_limit)
        # Get the list of pool block(s) heights
        if height == 0:
            blocks = Pool_blocks.get_latest(range)
        else:
            blocks = Pool_blocks.get_by_height(height, range)
        block_heights = [pb.height for pb in blocks]
        # Get estimates for each of the blocks
        estimates = {}
        for height in block_heights:
            estimate = 0
            payout_map = pool.get_block_payout_map_estimate(height, LOGGER)
            if payout_map is None:
                estimate = "TBD"
            elif id_str in payout_map:
                estimate = payout_map[id_str]
            else:
                estimate = 0
            str_height = str(height)
            estimates[str_height] = estimate
        return estimates

api.add_resource(EstimateApi_payment,
        '/worker/estimate/payment/<int:id>', 
        '/worker/estimate/payment/<int:id>/<int:height>', 
        '/worker/estimate/payment/<int:id>/<int:height>,<int:range>', 
        '/worker/estimate/payment/<int:id>/<string:height>', 
)

class EstimateApi_pooldailyearning(Resource):
    @cache.cached(timeout=120)
    def get(self, height=0, gps=1):
        return pool.estimated_daily_reward(gps, height)

api.add_resource(EstimateApi_pooldailyearning,
        '/pool/estimate/dailyearning', 
        '/pool/estimate/dailyearning/<int:height>', 
        '/pool/estimate/dailyearning/<int:height>/<float:gps>', 
        '/pool/estimate/dailyearning/<int:height>/<int:gps>', 
)

##
# Call "Payment API" service from this proxy endpoint
##
# Payment REQUESTs
class PoolAPI_paymentrequest(Resource):
    #decorators = [limiter.limit("5/minute"), auth.login_required]
    @auth.login_required
    def post(self, id, function, address=None):
        global database
        LOGGER = lib.get_logger(PROCESS)
        debug = True
        debug and LOGGER.warn("PoolAPI_paymentrequest POST: {} - {}".format(id, function))
        # AUTH FILTER
        if id != g.user.id:
            response = jsonify({ 'message': 'Not authorized to access data for other users' })
            response.status_code = 403
            return response
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        #if id != 573: # foo16 on bitmugle pool for testing
        #    LOGGER.warn("Payments are disabled")
        #    response = jsonify({ 'message': 'Payouts are temporarily disabled' })
        #    response.status_code = 400
        #    return response
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        # XXX TODO: Get from config
        payment_req_url = "http://payment_api:3425"
        # Get the users balance then call the internal payment request api to
        # generate a payment tx slate.  Return that slate to the caller
        if function == "get_tx_slate":
            # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
            #LOGGER.warn("SLATE payment requests are disabled")
            #response = jsonify({ 'message': 'File-Based payouts are temporarily disabled' })
            #response.status_code = 400
            #return response
            # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
            ##
            # Offline Phase 1) issue_send_tx
            # Generate the send transaction slate
            utxo = Pool_utxo.get_by_userid(id)
            amount = utxo.amount
            user_id = str(utxo.user_id)
            # XXX TODO: Check if greater than minimum payout
            get_tx_slate_url = payment_req_url + "/pool/payment/get_tx_slate/"+user_id
            debug and LOGGER.warn("Requesting Payment slate: {}".format(get_tx_slate_url))
            r = requests.post(
                    url=get_tx_slate_url,
                    auth=(admin_user, admin_pass)
                )
            debug and LOGGER.warn("get_tx_slate call: {} - {}".format(r.status_code, r.reason))
            if r.status_code != 200:
                LOGGER.warn("Failed to get a payment slate: {} - {} - {}".format(r.status_code, r.reason, r.json()["message"]))
                response = jsonify({ 'message': 'Failed to get a payment slate: {}'.format(r.json()["message"])})
                response.status_code = r.status_code
                return response
            return(json.loads(r.text))
        elif function == "submit_tx_slate":
            ##
            # Offline Phase 2) finalize_tx
            # Submit the signed slate to be finalized
            debug and LOGGER.warn("submit_slate: {}".format(id))
            try:
                requestdata = request.data
                rdjson = json.loads(requestdata.decode('utf-8'))
                debug and LOGGER.warn("PoolAPI_paymentrequest POST: requestdata:{}".format(rdjson))
            except AttributeError as e:
                LOGGER.warn("Missing tx_slate data - {}".format(request.data))
                response = jsonify({ 'message': 'Missing signed slate data' })
                response.status_code = 400
                return response
            except json.decoder.JSONDecodeError:
                LOGGER.warn("Invalid tx_slate data - {}".format(request.data))
                response = jsonify({ 'message': 'Invalid signed slate data was submitted' })
                response.status_code = 400
                return response
            debug and LOGGER.warn("submit_slate: {}".format(requestdata))
            submit_tx_slate_url = payment_req_url + "/pool/payment/submit_tx_slate/"+str(id)
            r = requests.post(
                    url=submit_tx_slate_url, 
                    data=requestdata,
                    auth=(admin_user, admin_pass)
                )
            if r.status_code != 200:
                LOGGER.warn("Failed to submit payment slate: {} - {} - {}".format(r.status_code, r.reason, r.json()["message"]))
                response = jsonify({ 'message': 'Failed to submit payment slate: {}'.format(r.json()["message"]) })
                response.status_code = r.status_code
                return response
            debug and LOGGER.warn("submit_tx_slate result: {} - {}".format(r.status_code, r.text))
            return "ok"
        elif function == "http":
            # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
            #if id != 573: # foo16 on bitmugle pool for testing
            #    LOGGER.warn("HTTP payment requests are disabled")
            #    response = jsonify({ 'message': 'HTTP payouts are temporarily disabled' })
            #    response.status_code = 400
            #    return response
            # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
            ##
            # Online Wallet-To-Wallet
            debug and LOGGER.warn("Send HTTP transaction: {}".format(id))
            LOGGER.warn("request.args: {}".format(request.args))
            if address is None:
                LOGGER.warn("HTTP payment request missing address")
                response = jsonify({ 'message': 'Error, must specify a wallet address:port' })
                response.status_code = 400
                return response
            debug and LOGGER.warn("Initiate HTTP payment: {} - {}  - {}".format(id, address, request.args))
            LOGGER.warn("Args in json: {}".format(json.dumps(request.args)))
            http_payment_url = payment_req_url + "/pool/payment/http/{}/{}".format(id, address)
            r = requests.post(
                    url=http_payment_url,
                    data=json.dumps(request.args),
                    headers={'content-type': 'application/json'},
                    auth=(admin_user, admin_pass)
                )
            if r.status_code != 200:
                LOGGER.warn("Failed to complete HTTP payment: {} - {}".format(r.status_code, r.reason))
                response = jsonify({ 'message': 'Failed to complete HTTP payment: {}'.format(r.json()["message"]) })
                response.status_code = r.status_code
                return response
            debug and LOGGER.warn("http payment result: {} - {}".format(r.status_code, r.text))
            return "ok"
        elif function == "keybase":
            ##
            # Online Wallet-To-Keybase-To-Keybase-To-Wallet
            debug and LOGGER.warn("Send keybase transaction: {}".format(id))
            if address is None:
                LOGGER.warn("keybase payment request missing address")
                response = jsonify({ 'message': 'Error, must specify a keybase username to send to' })
                response.status_code = 400
                return response
            debug and LOGGER.warn("Initiate keybase payment: {} - {}".format(id, address))
            keybase_payment_url = payment_req_url + "/pool/payment/keybase/{}/{}".format(id, address)
            r = requests.post(
                    url=keybase_payment_url, 
                    auth=(admin_user, admin_pass)
                )
            if r.status_code != 200:
                LOGGER.warn("Failed to complete keybase payment: {} - {}".format(r.status_code, r.reason))
                response = jsonify({ 'message': 'Failed to complete keybase payment: {}'.format(r.json()["message"]) })
                response.status_code = r.status_code
                return response
            debug and LOGGER.warn("keybase payment result: {} - {}".format(r.status_code, r.text))
            return "ok"
        elif function == "payout_script":
            ##
            # Not really a payout request, rather, a request for payout automation script code
            debug and LOGGER.warn("Get Payout Script: {}".format(id))
            #file = open("/content/BGP_payout.py", "r")
            #payout_script = file.read() 
            #return payout_script
            return send_from_directory('/content', 'GP_payout.py')
        else:
            LOGGER.warn("Invalid Payment Type requested")
            response = jsonify({ 'message': 'Error, must specify valid payment request method.  Method {} is not valid.'.format(function) })
            response.status_code = 400
            return response

            
api.add_resource(PoolAPI_paymentrequest,
        '/pool/payment/<string:function>/<int:id>', 
        '/pool/payment/<string:function>/<int:id>/<path:address>', 
)









# Start the API server 
# gunicorn "a real webserver" is called from k8s spec -0 this is here for debugging
if __name__ == '__main__':
    database = lib.get_db()
    app.run(debug=False, host='0.0.0.0', port=13423)
