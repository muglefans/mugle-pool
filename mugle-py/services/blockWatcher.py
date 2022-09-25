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

# Watches the blockchain for new blocks
#  Request chain height from mugle core every x seconds.
#  If the height increased request each block from mugle core.
#  Adds them to the database.
# This keeps a record of each block *as we see it* (before any chain reorgs).

import sys
import traceback
import requests
import json
import atexit
from time import sleep
from datetime import datetime

import pymysql
import sqlalchemy

from muglelib import lib
from muglelib import mugle
from muglebase.model.blocks import Blocks

PROCESS = "blockWatcher"
LOGGER = None
CONFIG = None

BATCHSZ = 100

def main():
    global CONFIG
    global LOGGER
    CONFIG = lib.get_config()
    LOGGER = lib.get_logger(PROCESS)
    LOGGER.warn("=== Starting {}".format(PROCESS))
    # Connect to DB
    database = lib.get_db()
    atexit.register(lib.teardown_db)

    # Get Config
    check_interval = float(CONFIG[PROCESS]["check_interval"])

    # Find the height of the latest block
    current_height = mugle.blocking_get_current_height()
    while current_height <= 0:
        LOGGER.warn("Waiting for first block height")
        sleep(10)
        current_height = mugle.blocking_get_current_height()
    LOGGER.warn("current_height = {}".format(current_height))

    latest_block = Blocks.get_latest()
    if latest_block is None:
        last_height = current_height - 1500
    else:
        last_height = latest_block.height 
    LOGGER.warn("last_height = {}".format(last_height))
    height = last_height + 1
    height = max(current_height-1500, height)
    LOGGER.warn("Starting at block height: {}".format(height))

    while True:
        try:
            latest = mugle.blocking_get_current_height()
            LOGGER.warn("latest: {}, height: {}".format(latest, height))
            while latest >= height:
                response = mugle.blocking_get_block_by_height(height)
                LOGGER.warn("New Block: {} at {}".format(response["header"]["hash"],
                                                         response["header"]["height"]))
                try:
                    new_block = Blocks(hash = response["header"]["hash"],
                                   version = response["header"]["version"],
                                   height = response["header"]["height"],
                                   previous = response["header"]["previous"],
                                   timestamp = datetime.strptime(response["header"]["timestamp"][:-1], "%Y-%m-%dT%H:%M:%S+00:0"),
                                   output_root = response["header"]["output_root"],
                                   range_proof_root = response["header"]["range_proof_root"],
                                   kernel_root = response["header"]["kernel_root"],
                                   nonce = response["header"]["nonce"],
                                   edge_bits = response["header"]["edge_bits"],
                                   total_difficulty = response["header"]["total_difficulty"],
                                   secondary_scaling = response["header"]["secondary_scaling"],
                                   num_inputs = len(response["inputs"]),
                                   num_outputs = len(response["outputs"]),
                                   num_kernels = len(response["kernels"]),
                                   fee = sum(k["fee"] for k in response["kernels"]),
                                   lock_height = response["kernels"][0]["lock_height"] if(len(response["kernels"])>0) else 0,
                                   total_kernel_offset = response["header"]["total_kernel_offset"],
                                   state = "new")
                    # Batch inserts when catching up
                    database.db.getSession().add(new_block)
                    if( (height % BATCHSZ == 0) or (height >= (latest-10)) ):
                        database.db.getSession().commit()
                    height = height + 1
                except (sqlalchemy.exc.IntegrityError, pymysql.err.IntegrityError):
                    LOGGER.warn("Attempted to re-add block: {}".format(response["header"]["height"]))
                    database.db.getSession().rollback()
                    latest_block = Blocks.get_latest()
                    height = latest_block.height + 1
                    sleep(check_interval)
            sys.stdout.flush()
            sleep(check_interval)
        except Exception as e:
            LOGGER.exception("Something went wrong: {}".format(repr(e)))
            database.db.getSession().rollback()
            sys.stdout.flush()
            sleep(check_interval)
    # Should never get here, but....
    LOGGER.warn("=== Completed {}".format(PROCESS))


if __name__ == "__main__":
    main()
