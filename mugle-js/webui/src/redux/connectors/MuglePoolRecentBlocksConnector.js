
import { connect } from 'react-redux'
import { BlockRange } from '../../containers/BlockRange/BlockRange.js'
import { fetchMuglePoolRecentBlocks } from '../actions/muglePoolDataActions.js'

const mapStateToProps = (state) => {
  return {
    latestBlockHeight: state.networkData.latestBlock.height,
    recentBlocks: state.muglePoolData.recentBlocks || [],
    graphTitle: 'Blocks Found by Pool'
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    fetchBlockRange: (endBlockHeight?: null | number, rangeSize?: number) => dispatch(fetchMuglePoolRecentBlocks(endBlockHeight, rangeSize))
  }
}

export const MuglePoolRecentBlocksConnector = connect(mapStateToProps, mapDispatchToProps)(BlockRange)
