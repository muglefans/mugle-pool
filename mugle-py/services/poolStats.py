#!/usr/bin/python

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

# Add a pool stats record ~per block


import sys
import requests
import json
import atexit
from time import sleep
import traceback


from muglebase.dbaccess import database

from muglelib import lib
from muglelib import mugle
from muglelib import poolstats

from muglebase.model.blocks import Blocks
from muglebase.model.pool_stats import Pool_stats
from muglebase.model.worker_shares import Worker_shares

PROCESS = "poolStats"
LOGGER = None
CONFIG = None

# XXX TODO: Move to config
BATCHSZ = 10

def main():
    CONFIG = lib.get_config()
    LOGGER = lib.get_logger(PROCESS)
    LOGGER.warn("=== Starting {}".format(PROCESS))
    # Connect to DB
    database = lib.get_db()
    atexit.register(lib.teardown_db)

    # Get config
    check_interval = float(CONFIG[PROCESS]["check_interval"])
    avg_over_range = int(CONFIG[PROCESS]["avg_over_range"])

    # Initialize poolStats records if this is the first run
    latest_stat = Pool_stats.get_latest()
    if latest_stat is None:
        # Special case for new pool startup
        poolstats.initialize(avg_over_range, LOGGER)

    latest_stat = Pool_stats.get_latest()
    LOGGER.warn("Starting at height: {}".format(latest_stat.height))

    # Generate pool stats records - one per mugle block
    while True:
        # Find the height of the latest stats record
        latest_stat = Pool_stats.get_latest()
        height = latest_stat.height + 1
        LOGGER.warn("Starting at height: {}".format(height))
        try:
            while True:
                share_height = Worker_shares.get_latest_height()
                while share_height is None:
                    LOGGER.warn("Waiting for shares")
                    share_height = Worker_shares.get_latest_height()
                    sleep(10)
                latest = Blocks.get_latest().height
                stats_height = height-1
                LOGGER.warn("Running: Chain height: {}, share height: {},  stats height: {}".format(latest, share_height, stats_height))
                while share_height-1 > height:
                    new_stats = poolstats.calculate(height, avg_over_range)
                    # Batch new stats when possible, but commit at reasonable intervals
                    database.db.getSession().add(new_stats)
                    if( (height % BATCHSZ == 0) or (height >= (latest-10)) ):
                        database.db.getSession().commit()
                    LOGGER.warn("Added Pool_stats for block: {} - {} {} {}".format(new_stats.height, new_stats.gps, new_stats.active_miners, new_stats.shares_processed))
                    height = height + 1
                    sys.stdout.flush()
                sleep(check_interval)
        except Exception as e:
            LOGGER.error("Something went wrong: {} - {}".format(e, traceback.print_stack()))
            database.db.getSession().rollback()
            sleep(check_interval)

    LOGGER.warn("=== Completed {}".format(PROCESS))

if __name__ == "__main__":
    main()
