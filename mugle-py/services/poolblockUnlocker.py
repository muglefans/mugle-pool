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

# Checks blocks found by the pool to see if they are ready to be unlocked and made available for payout.
#

import os
import sys
import requests
import json
import time

from muglelib import lib
from muglelib import mugle
from muglelib import wallet
from muglebase.model.pool_blocks import Pool_blocks

PROCESS = "poolblockUnlocker"
LOGGER = None
CONFIG = None

# Get K8s secret from container environment
wallet_api_user = os.environ['WALLET_OWNER_API_USER']
wallet_api_key = os.environ["WALLET_OWNER_API_PASSWORD"]

def main():
    CONFIG = lib.get_config()
    LOGGER = lib.get_logger(PROCESS)
    LOGGER.warn("=== Starting {}".format(PROCESS))
    # Connect to DB
    database = lib.get_db()

    # Get the list of pool_blocks that are
    # old enough to unlock and
    # are not orphan blocks

    # XXX TODO: The node may not be synced, may need to wait?

    block_locktime = int(CONFIG[PROCESS]["block_locktime"])
    block_expiretime = int(CONFIG[PROCESS]["block_expiretime"])
    LOGGER.warn("using locktime: {}, expiretime: {}".format(block_locktime, block_expiretime))

    latest = mugle.blocking_get_current_height()
    LOGGER.warn("Latest: {}".format(latest))

    # Get outputs form the wallet
    wallet_outputs = wallet.retrieve_outputs(refresh=True)
    wallet_outputs_map = wallet.outputs_to_map_by_height(wallet_outputs)
    wallet_output_heights = list(wallet_outputs_map.keys())
    wallet_output_heights.sort()
    #print("wallet_output_heights = {}".format(wallet_output_heights))

    new_poolblocks = Pool_blocks.get_all_new()
    for pb in new_poolblocks:
        if pb.height < (latest - block_expiretime):
            # Dont re-process very old blocks - protection against duplicate payouts.
            LOGGER.error("Processed expired pool block at height: {}".format(pb.height))
            pb.state = "expired"
            continue
        response = mugle.get_block_by_height(pb.height)
        # Check for unknown block
        if response == None:
            # Unknown.  Leave as "new" for now and attempt to validate next run
            LOGGER.error("Failed to get block {}".format(pb.height))
            continue
        # Check for orphans
        if int(response["header"]["nonce"]) != int(pb.nonce):
            LOGGER.warn("Processed orphan pool block at height: {}".format(pb.height))
            pb.state = "orphan"
            continue
#        # Check that we have a coinbase output in the wallet for this block
#        if pb.height not in wallet_output_heights:
#            LOGGER.warn("Wallet has no output for pool block at height: {}".format(pb.height))
#            pb.state = "no_wallet_output"
#            continue
        # Check if its old enough to be mature
        if pb.height < (latest - block_locktime):
            # This block seems valid, and old enough to unlock
            LOGGER.warn("Unlocking pool block at height: {}".format(pb.height))
            pb.state = "unlocked"
        sys.stdout.flush()

    # db.set_last_run(PROCESS, str(time.time()))
    database.db.getSession().commit()
    LOGGER.warn("=== Completed {}".format(PROCESS))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
