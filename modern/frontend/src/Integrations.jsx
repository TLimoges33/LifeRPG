import React, {useState, useEffect} from 'react'

const API = (path) => fetch(path, {credentials: 'include'}).then(r => r.json())

export default function Integrations(){
  const [integrations, setIntegrations] = useState([])
  const [events, setEvents] = useState(null)
  const [userId] = useState(1)

  useEffect(()=>{
    API(`/api/v1/users/${userId}/integrations`).then(d=>setIntegrations(d)).catch(()=>setIntegrations([]))
  }, [userId])

  function startGoogle(){
    // Open backend OAuth URL in new window so the redirect can complete
    window.open(`/api/v1/oauth/google/login?user_id=${userId}`, '_blank')
  }

  function fetchEvents(integrationId){
    API(`/api/v1/integrations/${integrationId}/google/events`).then(d=>setEvents(d)).catch(e=>setEvents({error: String(e)}))
  }

  return (
    <div style={{marginTop:20}}>
      <h2>Integrations</h2>
      <button onClick={startGoogle}>Connect Google Calendar</button>
      <h3>Your Integrations</h3>
      <ul>
        {integrations && integrations.length ? integrations.map(i=> (
          <li key={i.id}>
            {i.provider} — id: {i.id} — user: {i.user_id} <button style={{marginLeft:8}} onClick={()=>fetchEvents(i.id)}>Fetch Events</button>
          </li>
        )): <li>No integrations</li>}
      </ul>
      <h3>Events</h3>
      <pre style={{whiteSpace:'pre-wrap',background:'#f6f6f6',padding:10}}>{events? JSON.stringify(events, null, 2): 'No events fetched'}</pre>
    </div>
  )
}
