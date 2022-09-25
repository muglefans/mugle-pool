
import { connect } from 'react-redux'
import { MuglePoolSharesSubmittedComponent } from '../../containers/MuglePoolData/MuglePoolSharesSubmitted.js'
import { fetchMuglePoolSharesSubmitted } from '../actions/muglePoolDataActions.js'

const mapStateToProps = (state) => {
  return {
    sharesSubmitted: state.muglePoolData.sharesSubmitted,
    latestBlockHeight: state.networkData.latestBlock.height || 0
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    fetchMuglePoolSharesSubmitted: () => dispatch(fetchMuglePoolSharesSubmitted())
  }
}

export const MuglePoolSharesSubmittedConnector = connect(mapStateToProps, mapDispatchToProps)(MuglePoolSharesSubmittedComponent)
