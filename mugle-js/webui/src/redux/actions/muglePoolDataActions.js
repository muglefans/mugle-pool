// @flow
import { API_URL_V2 } from '../../config.js'
import { BLOCK_RANGE } from '../../constants/dataConstants.js'
import { type Dispatch, type GetState } from '../../types.js'

export const fetchMuglePoolData = (start: number = 0) => async (dispatch: Dispatch, getState: GetState) => {
  try {
    const state = getState()
    const latestBlockHeight = state.networkData.latestBlock.height || 0
    if (latestBlockHeight === 0) return
    const previousData = state.muglePoolData.historical
    let previousMaxBlockHeight = latestBlockHeight - BLOCK_RANGE
    previousData.forEach(block => {
      if (block.height > previousMaxBlockHeight) previousMaxBlockHeight = block.height
    })
    const blockDifference = latestBlockHeight - previousMaxBlockHeight
    const url = `${API_URL_V2}pool/stats/${latestBlockHeight},${blockDifference}/gps,height,total_blocks_found,active_miners,timestamp,edge_bits`
    const newMuglePoolDataResponse = await fetch(url)
    if (!newMuglePoolDataResponse.ok) return
    const newMuglePoolData = await newMuglePoolDataResponse.json()
    const newFormattedMuglePoolData = newMuglePoolData.map((block) => {
      return {
        ...block,
        share_counts: JSON.parse(block.share_counts)
      }
    })
    const concatenatedMuglePoolData = [...previousData, ...newFormattedMuglePoolData]
    const numberToRemove = concatenatedMuglePoolData.length > BLOCK_RANGE ? concatenatedMuglePoolData.length - BLOCK_RANGE : 0
    const newHistoricalData = concatenatedMuglePoolData.slice(numberToRemove)
    dispatch({ type: 'MUGLE_POOL_DATA', data: { historical: newHistoricalData } })
  } catch (e) {
    console.log('Error: ', e)
  }
}

export const fetchMuglePoolLastBlock = (start: number = 0) => async (dispatch: Dispatch, getState: GetState) => {
  try {
    const url = `${API_URL_V2}pool/block`
    const muglePoolLastBlockDataResponse = await fetch(url)
    if (!muglePoolLastBlockDataResponse.ok) return
    const muglePoolLastBlockData = await muglePoolLastBlockDataResponse.json()
    dispatch({ type: 'MUGLE_POOL_LAST_BLOCK_MINED', data: { lastBlockMined: muglePoolLastBlockData.timestamp } })
  } catch (e) {
    console.log('Error: ', e)
  }
}

export const fetchMuglePoolRecentBlocks = () => async (dispatch: Dispatch, getState: GetState) => {
  try {
    const state = getState()
    const minedBlockAlgos = state.networkData.minedBlockAlgos
    const latestBlockHeight = state.networkData.latestBlock.height || 0
    if (latestBlockHeight === 0) return
    const url = `${API_URL_V2}pool/blocks/${latestBlockHeight},20`
    const muglePoolRecentBlocksResponse = await fetch(url)
    if (!muglePoolRecentBlocksResponse.ok) return
    const muglePoolRecentBlocksData = await muglePoolRecentBlocksResponse.json()
    const muglePoolRecentBlockWithEdgeBits = muglePoolRecentBlocksData.map(block => {
      let edge_bits = 29
      if (minedBlockAlgos.c31.includes(block.height)) edge_bits = 31
      return {
        ...block,
        edge_bits
      }
    })
    dispatch({
      type: 'MUGLE_POOL_RECENT_BLOCKS',
      data: muglePoolRecentBlockWithEdgeBits
    })
  } catch (e) {

  }
}

export const fetchMuglePoolSharesSubmitted = (start: number = 0) => async (dispatch: Dispatch, getState: GetState) => {
  try {
    const state = getState()
    const latestBlockHeight = state.networkData.latestBlock.height || 0
    if (latestBlockHeight === 0) return
    const previousData = state.muglePoolData.sharesSubmitted
    let previousMaxBlockHeight = latestBlockHeight - BLOCK_RANGE
    previousData.forEach(block => {
      if (block.height > previousMaxBlockHeight) previousMaxBlockHeight = block.height
    })
    const blockDifference = latestBlockHeight - previousMaxBlockHeight
    const url = `${API_URL_V2}pool/stats/${latestBlockHeight},${blockDifference}/shares_processed,total_shares_processed,active_miners,height`
    const newSharesSubmittedDataResponse = await fetch(url)
    if (!newSharesSubmittedDataResponse.ok) return
    const newSharesSubmittedData = await newSharesSubmittedDataResponse.json()
    const concatenatedMuglePoolShareData = [...previousData, ...newSharesSubmittedData]
    const numberToRemove = concatenatedMuglePoolShareData.length > BLOCK_RANGE ? concatenatedMuglePoolShareData.length - BLOCK_RANGE : 0
    const sharesSubmittedData = concatenatedMuglePoolShareData.slice(numberToRemove)
    dispatch({ type: 'MUGLE_POOL_SHARES_SUBMITTED', data: { sharesSubmittedData } })
  } catch (e) {
    console.log('Error: ', e)
  }
}

export const fetchMuglePoolBlocksMined = () => async (dispatch: Dispatch, getState: GetState) => {
  try {
    const state = getState()
    const minedBlockAlgos = state.networkData.minedBlockAlgos
    const previousData = {
      ...state.muglePoolData.poolBlocksMined,
      orphaned: state.muglePoolData.poolBlocksOrphaned
    }
    const latestBlockHeight = state.networkData.latestBlock.height || 0
    if (latestBlockHeight === 0) return
    let combinedMaxBlockHeight = Math.max(Math.max(...previousData.c29), Math.max(...previousData.c31), Math.max(...previousData.orphaned))
    combinedMaxBlockHeight = isFinite(combinedMaxBlockHeight) ? combinedMaxBlockHeight : 0
    const blockDifference = combinedMaxBlockHeight ? (latestBlockHeight - combinedMaxBlockHeight) : BLOCK_RANGE
    const url = `${API_URL_V2}pool/blocks/${latestBlockHeight},${blockDifference}`
    const muglePoolBlocksMinedResponse = await fetch(url)
    if (!muglePoolBlocksMinedResponse.ok) return
    const muglePoolBlocksMinedData = await muglePoolBlocksMinedResponse.json()
    // turn them into a basic array
    const c29BlocksFound = []
    const c31BlocksFound = []
    const c29BlocksWithTimestamps = {}
    const c31BlocksWithTimestamps = {}
    const blocksOrphaned = []
    muglePoolBlocksMinedData.forEach((block) => {
      if (block.state === 'new') {
        if (minedBlockAlgos.c29.includes(block.height)) {
          c29BlocksFound.push(block.height)
          c29BlocksWithTimestamps[block.height] = { height: block.height, timestamp: block.timestamp }
        }
        if (minedBlockAlgos.c31.includes(block.height)) {
          c31BlocksFound.push(block.height)
          c31BlocksWithTimestamps[block.height] = { height: block.height, timestamp: block.timestamp }
        }
      } else if (block.state === 'orphan') {
        blocksOrphaned.push(block.height)
      }
    })
    const updatedPoolBlocksMined = {
      c29: [...previousData.c29, ...c29BlocksFound],
      c31: [...previousData.c31, ...c31BlocksFound],
      orphaned: [...previousData.orphaned, ...blocksOrphaned],
      c29WithTimestamps: { ...previousData.c29BlocksWithTimestamps, ...c29BlocksWithTimestamps },
      c31WithTimestamps: { ...previousData.c31BlocksWithTimestamps, ...c31BlocksWithTimestamps }
    }
    updatedPoolBlocksMined.c29.filter(height => (height > latestBlockHeight - BLOCK_RANGE))
    updatedPoolBlocksMined.c31.filter(height => (height > latestBlockHeight - BLOCK_RANGE))
    updatedPoolBlocksMined.orphaned.filter(height => (height > latestBlockHeight - BLOCK_RANGE))
    dispatch({
      type: 'POOL_BLOCKS_MINED',
      data: {
        c29BlocksFound: updatedPoolBlocksMined.c29,
        c31BlocksFound: updatedPoolBlocksMined.c31,
        blocksOrphaned: updatedPoolBlocksMined.orphaned,
        c29BlocksWithTimestamps: updatedPoolBlocksMined.c29WithTimestamps,
        c31BlocksWithTimestamps: updatedPoolBlocksMined.c31WithTimestamps
      }
    })
  } catch (e) {
    console.log('getchMuglePoolBlocksMined error: ', e)
  }
}
