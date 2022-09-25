import { combineReducers, createStore, applyMiddleware, compose } from 'redux'
import thunk from 'redux-thunk'
import {
  sidebarReducer,
  themeReducer,
  networkDataReducer,
  muglePoolDataReducer,
  authReducer,
  minerDataReducer
} from '../redux/reducers/index'

const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose
const reducer = combineReducers({
  theme: themeReducer,
  sidebar: sidebarReducer,
  networkData: networkDataReducer,
  muglePoolData: muglePoolDataReducer,
  minerData: minerDataReducer,
  auth: authReducer
})
const store = createStore(reducer, composeEnhancers(applyMiddleware(thunk)))

export default store
