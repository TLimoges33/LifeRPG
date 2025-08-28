import React, { useState, useEffect } from 'react'

const API = (path) => fetch(path, { credentials: 'include' }).then(r => r.json())

export default function Integrations() {
    const [integrations, setIntegrations] = useState([])
    const [events, setEvents] = useState(null)
    const [userId] = useState(1)
    const [msg, setMsg] = useState(null)
    const [loadingId, setLoadingId] = useState(null)

    useEffect(() => {
        API(`/api/v1/users/${userId}/integrations`).then(d => setIntegrations(d)).catch(() => setIntegrations([]))
    }, [userId])

    function startGoogle() {
        // Open backend OAuth URL in new window so the redirect can complete
        window.open(`/api/v1/oauth/google/login?user_id=${userId}`, '_blank')
    }

    function fetchEvents(integrationId) {
        setLoadingId(integrationId)
        fetch(`/api/v1/integrations/${integrationId}/google/events`, { credentials: 'include' })
            .then(r => r.json())
            .then(d => {
                setEvents(d)
                setMsg('Fetched events')
            })
            .catch(e => setEvents({ error: String(e) }))
            .finally(() => setLoadingId(null))
    }

    function previewEvents(integrationId) {
        fetch(`/api/v1/integrations/${integrationId}/events_preview`, { credentials: 'include' })
            .then(r => r.json()).then(d => {
                setEvents(d)
                setMsg('Preview loaded')
            }).catch(() => setMsg('Preview failed'))
    }

    function removeIntegration(integrationId) {
        if (!confirm('Remove integration?')) return
        setLoadingId(integrationId)
        fetch(`/api/v1/integrations/${integrationId}`, { method: 'DELETE', credentials: 'include' })
            .then(r => r.json())
            .then(d => {
                setMsg('Integration removed')
                setIntegrations(integrations.filter(i => i.id !== integrationId))
            })
            .catch(e => setMsg('Failed to remove'))
            .finally(() => setLoadingId(null))
    }

    function syncIntegration(integrationId) {
        setLoadingId(integrationId)
        fetch(`/api/v1/integrations/${integrationId}/sync_to_habits`, { method: 'POST', credentials: 'include' })
            .then(r => r.json())
            .then(d => setMsg(`Synced ${d.count || 0} items`))
            .catch(e => setMsg('Sync failed'))
            .finally(() => setLoadingId(null))
    }

    return (
        <div style={{ marginTop: 20 }}>
            <h2>Integrations</h2>
            <button onClick={startGoogle}>Connect Google Calendar</button>
            <h3>Your Integrations</h3>
            <ul>
                {integrations && integrations.length ? integrations.map(i => (
                    <li key={i.id} style={{ marginBottom: 8 }}>
                        <strong>{i.provider}</strong> — id: {i.id} — user: {i.user_id}
                        <div style={{ display: 'inline-block', marginLeft: 12 }}>
                            <button onClick={() => fetchEvents(i.id)} disabled={loadingId === i.id} style={{ marginRight: 6 }}>Fetch Events</button>
                            <button onClick={() => previewEvents(i.id)} disabled={loadingId === i.id} style={{ marginRight: 6 }}>Preview</button>
                            <button onClick={() => syncIntegration(i.id)} disabled={loadingId === i.id} style={{ marginRight: 6 }}>Sync → Habits</button>
                            <button onClick={() => removeIntegration(i.id)} disabled={loadingId === i.id}>Remove</button>
                        </div>
                    </li>
                )) : <li>No integrations</li>}
            </ul>
            {msg && <div style={{ marginTop: 8, color: '#0366d6' }}>{msg}</div>}
            <h3>Events</h3>
            <pre style={{ whiteSpace: 'pre-wrap', background: '#f6f6f6', padding: 10 }}>{events ? JSON.stringify(events, null, 2) : 'No events fetched'}</pre>
        </div>
    )
}
