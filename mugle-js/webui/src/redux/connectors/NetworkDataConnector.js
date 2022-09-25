
import { connect } from 'react-redux'
import { NetworkDataComponent } from '../../containers/NetworkData/NetworkData.js'
import { fetchNetworkData } from '../actions/networkDataActions.js'
import { fetchMuglePoolRecentBlocks } from '../actions/muglePoolDataActions.js'

const mapStateToProps = (state) => {
  const networkData = state.networkData.historical || []
  const latestBlock = state.networkData.latestBlock || 0
  const poolBlocksMined = state.muglePoolData.poolBlocksMined || []
  const latestBlockHeight = state.networkData.latestBlock.height
  return {
    networkData,
    latestBlock,
    poolBlocksMined,
    latestBlockHeight
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    fetchNetworkData: () => dispatch(fetchNetworkData()),
    fetchMuglePoolRecentBlocks: () => dispatch(fetchMuglePoolRecentBlocks())
  }
}

export const NetworkDataConnector = connect(mapStateToProps, mapDispatchToProps)(NetworkDataComponent)
