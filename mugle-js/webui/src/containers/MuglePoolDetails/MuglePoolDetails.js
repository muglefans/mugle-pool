import React, { Component } from 'react'
import { Col, Container, Row, Card, CardBody } from 'reactstrap'
import { MuglePoolDataConnector } from '../../redux/connectors/MuglePoolDataConnector.js'
import { MuglePoolSharesSubmittedConnector } from '../../redux/connectors/MuglePoolSharesSubmittedConnector.js'
import { MuglePoolStatsTableConnector } from '../../redux/connectors/MuglePoolStatsTableConnector.js'
import { MuglePoolRecentBlocksConnector } from '../../redux/connectors/MuglePoolRecentBlocksConnector.js'
import ReactGA from 'react-ga'

export class MuglePoolDetailsComponent extends Component {
  constructor (props) {
    super(props)
    ReactGA.initialize('UA-132063819-1')
    ReactGA.pageview(window.location.pathname + window.location.search)
  }

  UNSAFE_componentWillMount () {

  }

  fetchMuglePoolData = () => {

  }

  render () {
    return (
      <Container className='dashboard'>
        <Row>
          <Col xs={12} md={12} lg={12} xl={12}>
            <h3 className='page-title'>MuglePool Details</h3>
          </Col>
        </Row>
        <Row>
          <Col xs={12} md={12} lg={12} xl={12}>
            <Card>
              <CardBody>
                <MuglePoolDataConnector />
              </CardBody>
            </Card>
          </Col>
        </Row>
        <Row>
          <Col xs={12} md={12} lg={12} xl={12}>
            <Card>
              <CardBody>
                <MuglePoolSharesSubmittedConnector />
              </CardBody>
            </Card>
          </Col>
        </Row>
        <Row>
          <Col xs={12} md={12} lg={12} xl={12}>
            <Card>
              <CardBody>
                <MuglePoolStatsTableConnector />
              </CardBody>
            </Card>
          </Col>
        </Row>
        <Row>
          <Col xs={12} md={12} lg={12} xl={12}>
            <Card>
              <CardBody>
                <MuglePoolRecentBlocksConnector />
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    )
  }
}
