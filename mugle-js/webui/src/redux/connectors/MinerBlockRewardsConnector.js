// @flow

import { connect } from 'react-redux'
import {
  MinerBlockRewards,
  type MinerBlockRewardsStateProps,
  type MinerBlockRewardsDispatchProps
} from '../../containers/MinerData/MinerBlockRewards.js'
import { fetchNetworkRecentBlocks, fetchNetworkData } from '../actions/networkDataActions.js'
import { fetchMinerShareData } from '../actions/minerDataActions.js'
import { fetchMuglePoolData } from '../actions/muglePoolDataActions.js'
import { type Dispatch, type State } from '../../types.js'

const mapStateToProps = (state: State): MinerBlockRewardsStateProps => {
  return {
    latestBlockHeight: state.networkData.latestBlock.height,
    recentBlocks: state.muglePoolData.recentBlocks || [],
    graphTitle: 'Miner Block Rewards',
    minerShareData: state.minerData.minerShareData,
    networkData: state.networkData.historical,
    muglePoolData: state.muglePoolData.historical
  }
}

const mapDispatchToProps = (dispatch: Dispatch): MinerBlockRewardsDispatchProps => {
  return {
    fetchBlockRange: (endBlockHeight?: null | number, rangeSize?: number) => dispatch(fetchNetworkRecentBlocks(endBlockHeight, rangeSize)),
    fetchMinerShareData: () => dispatch(fetchMinerShareData()),
    fetchNetworkData: () => dispatch(fetchNetworkData()),
    fetchMuglePoolData: () => dispatch(fetchMuglePoolData())
  }
}

export const MinerBlockRewardsConnector = connect(mapStateToProps, mapDispatchToProps)(MinerBlockRewards)
