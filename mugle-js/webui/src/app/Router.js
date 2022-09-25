import React, { Component } from 'react'
import { connect } from 'react-redux'
import { Route, Switch, Redirect } from 'react-router-dom'
import Layout from '../containers/_layout/Layout'
import MainWrapper from './MainWrapper'
import { MinerDetailsConnector } from '../redux/connectors/MinerDetailsConnector.js'
import { RigDetailsConnector } from '../redux/connectors/RigDetailsConnector.js'
import { MinerPaymentConnector } from '../redux/connectors/MinerPaymentConnector.js'
import { HomepageConnector } from '../redux/connectors/HomepageConnector.js'
import { InfoComponent } from '../containers/Info/Info.js'
import { MuglePoolDetailsConnector } from '../redux/connectors/MuglePoolDetailsConnector.js'
import { LoginConnector } from '../redux/connectors/LoginConnector.js'
import { TutorialsComponent } from '../containers/Instructions/Instructions.js'
import { TermsOfServiceComponent } from '../containers/TermsOfService/TermsOfService.js'
import { FAQComponent } from '../containers/FAQ/FAQ.js'

class Router extends Component {
  render () {
    return (
      <MainWrapper>
        <main>
          <Switch>
            <Route path='/' component={WrappedRoutesConnector}/>
          </Switch>
        </main>
      </MainWrapper>
    )
  }
}

class WrappedRoutes extends Component {
  render () {
    const { account } = this.props

    return (
      <div>
        <Layout/>
        <div className='container__wrap'>
          <Route exact path='/' component={HomepageConnector}/>
          <Route path='/pages' component={Pages}/>
          <Route path='/info' component={InfoComponent}/>
          <Route path='/pool' component={MuglePoolDetailsConnector} />
          <Route path="/login" component={LoginConnector} />
          <Route path="/faq" component={FAQComponent} />
          <Route path="/instructions" component={TutorialsComponent} />
          <Route path="/terms-of-service" component={TermsOfServiceComponent} />
          <PrivateRoute path="/miner" exact component={MinerDetailsConnector} account={account} />
          <PrivateRoute path="/rigs" exact component={RigDetailsConnector} account={account} />
          <PrivateRoute path="/miner/payment" component={MinerPaymentConnector} account={account} />
        </div>
      </div>
    )
  }
}

export const WrappedRoutesConnector = connect((state) => ({
  account: state.auth.account
}))(WrappedRoutes)

const Pages = () => (
  <Switch>
    <Route exact path='/' component={HomepageConnector}/>
  </Switch>
)

function PrivateRoute ({ component: Component, ...rest }) {
  return (
    <Route
      {...rest}
      render={props =>
        rest.account ? (
          <Component {...props} />
        ) : (
          <Redirect
            to={{
              pathname: '/login',
              state: { from: props.location }
            }}
          />
        )
      }
    />
  )
}

export default Router
