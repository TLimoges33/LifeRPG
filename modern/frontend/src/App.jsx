import React from 'react'
import Integrations from './Integrations'

export default function App(){
  return (
    <div style={{padding:20,fontFamily:'system-ui, sans-serif'}}>
      <h1>LifeRPG Modern</h1>
      <p>Welcome — frontend scaffold. Connect to backend at <code>/api/v1</code>.</p>
      <Integrations />
    </div>
  )
}
