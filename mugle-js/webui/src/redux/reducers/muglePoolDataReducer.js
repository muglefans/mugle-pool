// @flow

import { combineReducers } from 'redux'
import type { MuglePoolBlockData, PoolSharesSubmitted, Reducer, Action } from '../../types'

export type MuglePoolState = {
  historical: Array<any>,
  lastBlockMined: number,
  recentBlocks: Array<Object>,
  poolBlocksMined: {c29: Array<number>, c31: Array<number>},
  poolBlocksOrphaned: Array<any>,
  sharesSubmitted: Array<any>
}

export type MuglePoolHistoricalBlockAction = {
  data: {
    historical: Array<MuglePoolBlockData>
  },
  type: 'MUGLE_POOL_DATA'
}

export const historical = (state: Array<any> = [], action: MuglePoolHistoricalBlockAction) => {
  switch (action.type) {
    case 'MUGLE_POOL_DATA':
      return action.data.historical
    default:
      return state
  }
}

export type LastMuglePoolBlockMinedAction = { type: 'MUGLE_POOL_LAST_BLOCK_MINED', data: { lastBlockMined: number } }

export const lastBlockMined = (state: number = 0, action: LastMuglePoolBlockMinedAction) => {
  switch (action.type) {
    case 'MUGLE_POOL_LAST_BLOCK_MINED':
      return action.data.lastBlockMined
    default:
      return state
  }
}

// recent blocks found by pool with info
export const recentBlocks = (state: Array<Object> = [], action: { type: 'MUGLE_POOL_RECENT_BLOCKS', data: Array<MuglePoolBlockData>}) => {
  switch (action.type) {
    case 'MUGLE_POOL_RECENT_BLOCKS':
      return action.data
    default:
      return state
  }
}

export type PoolBlocksMinedAction = {
  type: 'POOL_BLOCKS_MINED',
  data: {
    c29BlocksFound: Array<number>,
    c31BlocksFound: Array<number>,
    c29BlocksWithTimestamps: { [number]: { height: number, timestamp: number }},
    c31BlocksWithTimestamps: { [number]: { height: number, timestamp: number }}
  }
}

// basic array of recent blocks found by pool
export const poolBlocksMined = (state: {c29: Array<number>, c31: Array<number>, c29BlocksWithTimestamps: Object, c31BlocksWithTimestamps: Object} = { c29: [], c31: [], c29BlocksWithTimestamps: {}, c31BlocksWithTimestamps: {} }, action: PoolBlocksMinedAction) => {
  switch (action.type) {
    case 'POOL_BLOCKS_MINED':
      return {
        c29: action.data.c29BlocksFound,
        c31: action.data.c31BlocksFound,
        c29BlocksWithTimestamps: action.data.c29BlocksWithTimestamps,
        c31BlocksWithTimestamps: action.data.c31BlocksWithTimestamps
      }
    default:
      return state
  }
}

export type PoolBlocksOrphanedAction = { type: 'POOL_BLOCKS_MINED', data: { blocksOrphaned: Array<number>}}

export const poolBlocksOrphaned = (state: Array<any> = [], action: PoolBlocksOrphanedAction) => {
  switch (action.type) {
    case 'POOL_BLOCKS_MINED':
      return action.data.blocksOrphaned
    default:
      return state
  }
}

export type PoolSharesSubmittedAction = { type: 'MUGLE_POOL_SHARES_SUBMITTED', data: { sharesSubmittedData: Array<PoolSharesSubmitted> }}

export const sharesSubmitted = (state: Array<any> = [], action: PoolSharesSubmittedAction) => {
  switch (action.type) {
    case 'MUGLE_POOL_SHARES_SUBMITTED':
      return action.data.sharesSubmittedData
    default:
      return state
  }
}

export const muglePoolData: Reducer<MuglePoolState, Action> = combineReducers({
  historical,
  lastBlockMined,
  recentBlocks,
  poolBlocksMined,
  poolBlocksOrphaned,
  sharesSubmitted
})
