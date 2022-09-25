import React, { Component } from 'react'
import { Row, Col, Table } from 'reactstrap'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { C29_COLOR, C31_COLOR } from '../../custom/custom.js'
import { MiningGraphConnector } from '../../redux/connectors/MiningGraphConnector.js'

export class NetworkDataComponent extends Component {
  constructor (props) {
    super(props)
    this.state = {
      faderStyleId: 'blockHeight1'
    }
  }
  UNSAFE_componentWillMount () {
    const { fetchNetworkData } = this.props
    fetchNetworkData()
  }

  componentDidUpdate (prevProps) {
    const { faderStyleId } = this.state
    const { latestBlockHeight, fetchNetworkData, fetchMuglePoolRecentBlocks } = this.props
    if (latestBlockHeight !== prevProps.latestBlockHeight) {
      fetchMuglePoolRecentBlocks()
      fetchNetworkData()
      this.setState({
        faderStyleId: faderStyleId === 'blockHeight1' ? 'blockHeight2' : 'blockHeight1'
      })
    }
  }

  render () {
    const { networkData, latestBlock, poolBlocksMined, latestBlockHeight } = this.props
    const { faderStyleId } = this.state
    let c29LatestGraphRate = 'C29 = 0 gps'
    let c31LatestGraphRate = 'C31 = 0 gps'
    let latestDifficulty = 'n/a'
    if (networkData.length > 0) {
      const lastBlock = networkData[networkData.length - 1]
      if (lastBlock.gps[0]) {
        c29LatestGraphRate = `C${lastBlock.gps[0].edge_bits} = ${lastBlock.gps[0].gps.toFixed(0)} gps`
      }
      if (lastBlock.gps[1]) {
        c31LatestGraphRate = `C${lastBlock.gps[1].edge_bits} = ${lastBlock.gps[1].gps.toFixed(0)} gps`
      }
      latestDifficulty = lastBlock.difficulty
    } else {
      c29LatestGraphRate = '0 gps'
      c31LatestGraphRate = '0 gps'
      latestDifficulty = 'n/a'
    }
    const nowTimestamp = Date.now()
    const latestBlockTimeAgo = latestBlock.timestamp ? Math.floor((nowTimestamp / 1000) - latestBlock.timestamp) : ''

    return (
      <Row xs={12} md={12} lg={12} xl={12}>
        <Col xs={12} md={12} lg={12} xl={12}>
          <MiningGraphConnector
            miningData={networkData}
            poolBlocksMined={poolBlocksMined}
            decimals={0}
          />
        </Col>
        <Col xs={12} md={12} lg={12} xl={12}>
          <h4 className='page-title' style={{ marginBottom: 36 }}>Network Stats</h4>
          <Table size='sm'>
            <tbody>
              <tr>
                <td><FontAwesomeIcon style={{ marginRight: 5 }} size='lg' icon={'chart-line'} /> Graph Rate</td>
                <td><span style={{ color: C29_COLOR }}>{c29LatestGraphRate}</span><br /><span style={{ color: C31_COLOR }}>{c31LatestGraphRate}</span></td>
              </tr>
              <tr>
                <td><FontAwesomeIcon style={{ marginRight: 5 }} size='lg' icon={'link'} />Chain Height</td>
                <td id={faderStyleId}>{latestBlockHeight}</td>
              </tr>
              <tr>
                <td><FontAwesomeIcon style={{ marginRight: 5 }} size='lg' icon={'clock'} /> Block Found</td>
                <td>{latestBlockTimeAgo} sec ago</td>
              </tr>
              <tr>
                <td><FontAwesomeIcon style={{ marginRight: 5 }} size='lg' icon={'desktop'} />Difficulty</td>
                <td>{latestDifficulty}</td>
              </tr>
              <tr>
                <td><FontAwesomeIcon style={{ marginRight: 5 }} size='lg' icon={'dollar-sign'} />Reward</td>
                <td>60 MUGLE / block</td>
              </tr>
            </tbody>
          </Table>
        </Col>
      </Row>
    )
  }
}

export class AnimatedText {
  render () {
    return (
      <span>{this.props.children}</span>
    )
  }
}
