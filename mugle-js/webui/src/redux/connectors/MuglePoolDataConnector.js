
import { connect } from 'react-redux'
import { MuglePoolDataComponent } from '../../containers/MuglePoolData/MuglePoolData.js'
import {
  fetchMuglePoolData,
  fetchMuglePoolLastBlock
} from '../actions/muglePoolDataActions.js'

const mapStateToProps = (state) => {
  const muglePoolHistoricalData = state.muglePoolData.historical
  const muglePoolHistoricalDataLength = muglePoolHistoricalData.length
  const poolBlocksMined = state.muglePoolData.poolBlocksMined
  const latestBlockHeight = state.networkData.latestBlock.height
  let activeWorkers = 0
  if (muglePoolHistoricalDataLength > 0) {
    activeWorkers = muglePoolHistoricalData[muglePoolHistoricalDataLength - 1].active_miners
  }
  return {
    muglePoolData: state.muglePoolData.historical || [],
    activeWorkers,
    lastBlockMined: state.muglePoolData.lastBlockMined,
    poolBlocksMined,
    latestBlockHeight
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    fetchMuglePoolData: () => dispatch(fetchMuglePoolData()),
    fetchMuglePoolLastBlock: () => dispatch(fetchMuglePoolLastBlock())
  }
}

export const MuglePoolDataConnector = connect(mapStateToProps, mapDispatchToProps)(MuglePoolDataComponent)
