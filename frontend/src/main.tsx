import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
// 确保 root 元素存在
const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element not found')
}
// 使用 React 18 的 createRoot API
ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)