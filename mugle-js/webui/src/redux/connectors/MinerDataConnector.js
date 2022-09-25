
import { connect } from 'react-redux'
import {
  MinerDataComponent,
  type MinerDataComponentDispatchProps,
  type MinerDataComponentStateProps
} from '../../containers/MinerData/MinerData.js'
import {
  fetchMinerData,
  fetchMinerPaymentData,
  fetchMinerImmatureBalance,
  getLatestMinerPaymentRange,
  fetchMinerShareData,
  fetchRigData,
  fetchMinerLatestBlockReward,
  fetchMinerNextBlockReward
} from '../actions/minerDataActions.js'
import { fetchNetworkData } from '../actions/networkDataActions.js'
import {
  fetchMuglePoolData,
  fetchMuglePoolRecentBlocks
} from '../actions/muglePoolDataActions.js'
import { type Dispatch } from '../../types.js'

const mapStateToProps = (state): MinerDataComponentStateProps => {
  const paymentData = state.minerData.paymentData
  return {
    minerData: state.minerData.historical || [],
    latestBlockHeight: state.networkData.latestBlock.height || 0,
    poolBlocksMined: state.muglePoolData.poolBlocksMined || { c29: [], c31: [] },
    latestBlockMugleEarned: state.minerData.latestBlockMugleEarned || 0,
    nextBlockMugleEarned: state.minerData.nextBlockMugleEarned || 0,
    latestBlock: state.networkData.latestBlock || 0,
    amount: paymentData.amount || 0,
    minerImmatureBalance: state.minerData.minerImmatureBalance || 0,
    totalPayoutsAmount: state.minerData.totalPayoutsAmount,
    minerShareData: state.minerData.minerShareData,
    networkData: state.networkData.historical,
    muglePoolData: state.muglePoolData.historical,
    muglePoolRecentBlocks: state.muglePoolData.recentBlocks,
    rigGpsData: state.minerData.rigGpsData
  }
}

const mapDispatchToProps = (dispatch: Dispatch): MinerDataComponentDispatchProps => {
  return {
    fetchMinerData: () => dispatch(fetchMinerData()),
    fetchMinerPaymentData: () => dispatch(fetchMinerPaymentData()),
    fetchMinerImmatureBalance: () => dispatch(fetchMinerImmatureBalance()),
    getLatestMinerPaymentRange: () => dispatch(getLatestMinerPaymentRange()),
    fetchMinerShareData: () => dispatch(fetchMinerShareData()),
    fetchNetworkData: () => dispatch(fetchNetworkData()),
    fetchMuglePoolData: () => dispatch(fetchMuglePoolData()),
    fetchMuglePoolRecentBlocks: () => dispatch(fetchMuglePoolRecentBlocks()),
    fetchRigData: () => dispatch(fetchRigData()),
    fetchMinerLatestBlockReward: () => dispatch(fetchMinerLatestBlockReward()),
    fetchMinerNextBlockReward: () => dispatch(fetchMinerNextBlockReward())
  }
}

export const MinerDataConnector = connect(mapStateToProps, mapDispatchToProps)(MinerDataComponent)
