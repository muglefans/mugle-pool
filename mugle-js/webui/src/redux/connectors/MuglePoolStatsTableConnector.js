
import { connect } from 'react-redux'
import { MuglePoolStatsTableComponent } from '../../containers/MuglePoolData/MuglePoolStatsTable'
import {
  fetchNetworkData
} from '../actions/networkDataActions.js'

const mapStateToProps = (state) => {
  return {
    historicalNetworkData: state.networkData.historical || [],
    historicalMuglePoolData: state.muglePoolData.historical || [],
    latestBlockHeight: state.networkData.latestBlock.height || 0
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    fetchNetworkData: () => dispatch(fetchNetworkData())
  }
}

export const MuglePoolStatsTableConnector = connect(mapStateToProps, mapDispatchToProps)(MuglePoolStatsTableComponent)
