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

# Add a worker stats record for each active user per block


import sys
import requests
import json
from time import sleep
import datetime
import traceback

from muglebase.dbaccess import database

from muglelib import lib
from muglelib import mugle
from muglelib import workerstats

from muglebase.model.blocks import Blocks
from muglebase.model.worker_stats import Worker_stats
from muglebase.model.worker_shares import Worker_shares
from muglebase.model.pool_stats import Pool_stats


PROCESS = "workerStats"
LOGGER = None
CONFIG = None

# XXX TODO: Move to config
DIFFICULTY = 29
BATCHSZ = 100


def main():
    CONFIG = lib.get_config()
    LOGGER = lib.get_logger(PROCESS)
    LOGGER.warn("=== Starting {}".format(PROCESS))
    # Connect to DB
    database = lib.get_db()

    # Get config
    check_interval = float(CONFIG[PROCESS]["check_interval"])
    avg_over_range = int(CONFIG[PROCESS]["avg_over_range"])

    # Find the height of the latest stats record
    last_height = 0
    latest_stat = Worker_stats.get_latest()
    
    if latest_stat != None:
        last_height = latest_stat.height
    else:
        latest = Blocks.get_latest()
        while latest is None:
            LOGGER.warn("Waiting for the first block...")
            sleep(10)
            latest = Blocks.get_latest()
        last_height = latest.height
    height = last_height + 1

    LOGGER.warn("Starting at block height: {}".format(height))

    # Generate worker stats records - one per mugle block for each active worker
    while True:
        # latest = mugle.blocking_get_current_height()
        latest = Blocks.get_latest().height
        share_height = Worker_shares.get_latest_height()
        while share_height is None:
            LOGGER.warn("waiting for the first worker shares")
            sleep(10)
            share_height = Worker_shares.get_latest_height()
        stats_height = height-1
        LOGGER.warn("Running: chain height: {}, share height: {} vs stats height: {}".format(latest, share_height, stats_height))
        while share_height > height:
            try:
                new_stats = workerstats.calculate(height, avg_over_range)
                LOGGER.warn("{} new stats for height {}".format(len(new_stats), height))
                for stats in new_stats:
                    LOGGER.warn("Added Worker_stats: {}".format(stats))
                # mark any existing pool_stats dirty
                pool_stats = Pool_stats.get_by_height(height)
                for stat_rec in new_stats:
                    database.db.getSession().add(stat_rec)
                if pool_stats is not None:
                    LOGGER.warn("Marked existing pool_stats dirty for height: {}".format(height))
                    pool_stats.dirty = True # Pool_stats need to be recalculated
                if( (height % BATCHSZ == 0) or (height >= (latest-10)) ):
                    LOGGER.warn("Commit ---")
                    database.db.getSession().commit()
                height = height + 1
            except Exception as e:
                LOGGER.exception("Something went wrong: {}".format(e))
                database.db.getSession().rollback()
                sleep(check_interval)
        sys.stdout.flush()
        sleep(check_interval)
    LOGGER.warn("=== Completed {}".format(PROCESS))


if __name__ == "__main__":
    main()
