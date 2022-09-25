#!/usr/bin/env python

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

#
# Routines for working with pool_stats records
#

import sys
import time
import requests
import json
from datetime import datetime
import pprint
pp = pprint.PrettyPrinter(indent=4)


from muglelib import lib
from muglelib import mugle

from muglebase.model.blocks import Blocks
from muglebase.model.mugle_stats import Mugle_stats
from muglebase.model.pool_stats import Pool_stats
from muglebase.model.pool_blocks import Pool_blocks
from muglebase.model.worker_shares import Worker_shares
from muglebase.model.gps import Gps


def estimate_gps_for_all_sizes(window):
    print("estimate_gps_for_all_sizes across all workers")
    sys.stdout.flush()
    if len(window) < 2:
        return []
    first_height = window[0].height
    last_height = window[-1].height
    first_mugle_block = Blocks.get_by_height(first_height)
    last_mugle_block = Blocks.get_by_height(last_height)
    assert first_mugle_block is not None, "Missing mugle block at height: {}".format(first_height)
    assert last_mugle_block is not None, "Missing mugle block at height: {}".format(last_height)
    valid_cnt = {}
    for pool_shares_rec in window:
        for shares in pool_shares_rec.shares:
            if shares.edge_bits not in valid_cnt:
                valid_cnt[shares.edge_bits] = 0
            valid_cnt[shares.edge_bits] += shares.valid
    print("Valid Share Counts entire window:")
    pp.pprint(valid_cnt)
    all_gps = []
    for sz, cnt in valid_cnt.items():
        gps = lib.calculate_graph_rate(window[0].timestamp, window[-1].timestamp, cnt, sz, last_height)
        all_gps.append((sz, gps, ))
    sys.stdout.flush()
    return all_gps


# Calculate the pool stats for the specified height
# Return a Pool_stats object
# Raises AssertionError
def calculate(height, window_size):
    # Get the most recent pool data from which to generate the stats
    previous_stats_record = Pool_stats.get_by_height(height-1)
    assert previous_stats_record is not None, "No previous Pool_stats record found"
    mugle_block = Blocks.get_by_height(height)
    assert mugle_block is not None, "Missing mugle block: {}".format(height)
    window = Worker_shares.get_by_height(height, window_size)
#    assert window[-1].height - window[0].height >= window_size, "Failed to get proper window size"
#    print("Sanity: window size:  {} vs  {}".format(window[-1].height - window[0].height, window_size))
    # Calculate the stats data
    timestamp = mugle_block.timestamp
    active_miners = len(list(set([s.user_id for s in window])))
    print("active_miners = {}".format(active_miners))
    # Keep track of share totals - sum counts of all share sizes submitted for this block
    num_shares_processed = 0
    share_counts = {}
    for ws in Worker_shares.get_by_height(height):
        num_shares_processed += ws.num_shares()
        for size in ws.sizes():
            size_str = "{}{}".format("C", size)
            if size_str not in share_counts:
                share_counts[size_str] = {"valid": 0, "invalid": 0, "stale": 0}
            share_counts[size_str] = { "valid": share_counts[size_str]["valid"] + ws.num_valid(size),
                                       "invalid": share_counts[size_str]["invalid"] + ws.num_invalid(size),
                                       "stale": share_counts[size_str]["stale"] + ws.num_stale(size)
                                     }
    print("num_shares_processed this block= {}".format(num_shares_processed))
    total_shares_processed = previous_stats_record.total_shares_processed + num_shares_processed
    total_blocks_found = previous_stats_record.total_blocks_found
    # Caclulate estimated GPS for all sizes with shares submitted
    all_gps = estimate_gps_for_all_sizes(window)
    if Pool_blocks.get_by_height(height-1) is not None:
        total_blocks_found = total_blocks_found + 1
    new_stats = Pool_stats(
            height = height,
            timestamp = timestamp,
            active_miners = active_miners,
            share_counts = share_counts,
            shares_processed = num_shares_processed,
            total_blocks_found = total_blocks_found,
            total_shares_processed = total_shares_processed,
            dirty = False,
        )
    print("all_gps for all pool workers")
    pp.pprint(all_gps)
    for gps_est in all_gps:
        gps_rec = Gps(
            edge_bits = gps_est[0],
            gps = gps_est[1]
        )
        new_stats.gps.append(gps_rec)
    sys.stdout.flush()
    return new_stats







# Re-Caclulate pool stats from the specified height and commits to DB
# Return height of the last stat recalculated
# Raises AssertionError
def recalculate(start_height, window_size):
    database = lib.get_db()
    height = start_height
    worker_shares_height = Worker_shares.get_latest_height() - 1
    while worker_shares_height > height:
        old_stats = Pool_stats.get_by_height(height)
        new_stats = calculate(height, window_size)
        if old_stats is None:
            database.db.createDataObj(new_stats)
        else:
            old_stats.timestamp = new_stats.timestamp
            old_stats.active_miners = new_stats.active_miners
            old_stats.share_counts = new_stats.share_counts
            old_stats.shares_processed = new_stats.shares_processed
            old_stats.total_blocks_found = new_stats.total_blocks_found
            old_stats.total_shares_processed = new_stats.total_shares_processed
            old_stats.dirty = False
            database.db.getSession().commit()
        height = height + 1


# Initialize Pool_stats
# No return value
def initialize(window_size, logger):
    database = lib.get_db()
    # Special case for new pool startup
    block_zero = None
    while block_zero is None:
        logger.warn("Waiting for the first block record in the database")
        time.sleep(1)
        block_zero = Blocks.get_earliest()
    print("block_zero={}".format(block_zero))
    
    stat_height = max(0, block_zero.height + window_size)
    seed_stat = Pool_stats(
            height=stat_height,
            timestamp=datetime.utcnow(),
            active_miners=0,
            shares_processed=0,
            share_counts=None,
            total_blocks_found=0,
            total_shares_processed=0,
            dirty = False,
        )
    database.db.createDataObj(seed_stat)
    seed_share = Worker_shares(
            height=stat_height,
            user_id=1,
            timestamp=datetime.utcnow(),
        )
    database.db.createDataObj(seed_share)

