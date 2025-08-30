import React, { useState, useEffect } from 'react'
import { api } from './api'

export default function Integrations() {
    const [integrations, setIntegrations] = useState([])
    const [events, setEvents] = useState(null)
    const [userId] = useState(1)
    const [msg, setMsg] = useState(null)
    const [loadingId, setLoadingId] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [adminSettings, setAdminSettings] = useState(null)
    const [providerCaps, setProviderCaps] = useState(null)
    const [details, setDetails] = useState({})
    const [hooksSchema, setHooksSchema] = useState(null)
    const [hooksExample, setHooksExample] = useState(null)
    const [orchestration, setOrchestration] = useState(null)
    const [autoRefresh, setAutoRefresh] = useState(false)
    const [refreshIntervalSec, setRefreshIntervalSec] = useState(10)
    const [sortKey, setSortKey] = useState('provider')
    const [sortDir, setSortDir] = useState('asc')
    const [orchLoading, setOrchLoading] = useState(false)

    useEffect(() => {
        setLoading(true); setError(null)
        api(`/v1/users/${userId}/integrations`).then(d => {
            setIntegrations(d)
            // fetch details for last sync display
            d.forEach(i => {
                api(`/v1/integrations/${i.id}`).then(info => {
                    setDetails(prev => ({ ...prev, [i.id]: info }))
                }).catch(() => { })
            })
        }).catch((e) => { setError(String(e)); setIntegrations([]) }).finally(() => setLoading(false))
        // load admin settings if available
        api('/v1/admin/settings').then(setAdminSettings).catch(() => { })
        api('/v1/admin/provider_caps').then(setProviderCaps).catch(() => { })
        api('/v1/admin/hooks/schema').then((d) => {
            setHooksSchema(d.schema || null)
            try {
                const ex = Array.isArray(d.examples) && d.examples.length ? d.examples[0] : null
                setHooksExample(ex && ex.hooks ? ex.hooks : null)
            } catch (_) { /* noop */ }
        }).catch(() => { })
        setOrchLoading(true)
        api('/v1/admin/orchestration').then(setOrchestration).catch(() => { }).finally(() => setOrchLoading(false))
    }, [userId])

    useEffect(() => {
        if (!autoRefresh) return
        const ms = Math.max(3, parseInt(String(refreshIntervalSec || 10), 10)) * 1000
        const id = setInterval(() => {
            setOrchLoading(true)
            api('/v1/admin/orchestration').then(setOrchestration).catch(() => { }).finally(() => setOrchLoading(false))
        }, ms)
        return () => clearInterval(id)
    }, [autoRefresh, refreshIntervalSec])

    function refreshOrchestration() {
        setOrchLoading(true)
        api('/v1/admin/orchestration').then(setOrchestration).catch(() => { }).finally(() => setOrchLoading(false))
    }

    function toggleSort(key) {
        if (sortKey === key) {
            setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
        } else {
            setSortKey(key)
            setSortDir('asc')
        }
    }

    function startGoogle() {
        // Open backend OAuth URL in new window so the redirect can complete
        window.open(`/api/v1/oauth/google/login?user_id=${userId}`, '_blank')
    }

    function fetchEvents(integrationId) {
        setLoadingId(integrationId)
        api(`/v1/integrations/${integrationId}/google/events`)
            .then(d => {
                setEvents(d)
                setMsg('Fetched events')
            })
            .catch(e => { setEvents({ error: String(e) }); setMsg('Fetch failed') })
            .finally(() => setLoadingId(null))
    }

    function previewEvents(integrationId) {
        api(`/v1/integrations/${integrationId}/events_preview`).then(d => {
            setEvents(d)
            setMsg('Preview loaded')
        }).catch(() => setMsg('Preview failed'))
    }

    function removeIntegration(integrationId) {
        if (!confirm('Remove integration?')) return
        setLoadingId(integrationId)
        api(`/v1/integrations/${integrationId}`, { method: 'DELETE' })
            .then(d => {
                setMsg('Integration removed')
                setIntegrations(integrations.filter(i => i.id !== integrationId))
            })
            .catch(e => setMsg('Failed to remove'))
            .finally(() => setLoadingId(null))
    }

    function syncIntegration(integrationId) {
        setLoadingId(integrationId)
        api(`/v1/integrations/${integrationId}/sync_to_habits`, { method: 'POST' })
            .then(d => setMsg(`Synced ${d.count || 0} items`))
            .catch(e => setMsg('Sync failed'))
            .finally(() => setLoadingId(null))
    }

    function setIntegrationConfig(id, patch) {
        // naive: fetch current integration then patch config server-side via a simple endpoint
        api(`/v1/integrations/${id}`).then(cur => {
            const cfg = { ...(cur.config ? JSON.parse(cur.config) : {}), ...patch }
            api(`/v1/integrations/${id}`, { method: 'PATCH', body: { config: cfg } })
                .then(() => setMsg('Settings updated'))
                .catch(() => setMsg('Failed to update settings'))
        }).catch(() => setMsg('Failed to load integration'))
    }

    return (
        <div style={{ marginTop: 20 }}>
            <h2>Integrations</h2>
            <button onClick={startGoogle}>Connect Google Calendar</button>
            {adminSettings && (
                <div style={{ marginTop: 8, padding: 8, background: '#f6f6f6' }}>
                    <strong>Admin Settings</strong>
                    <div style={{ marginTop: 6 }}>
                        <label style={{ marginRight: 6 }}>Close mode:</label>
                        <select defaultValue={adminSettings.integration_close_mode} onChange={(e) => {
                            api('/v1/admin/settings', { method: 'POST', body: { integration_close_mode: e.target.value } })
                                .then(() => setAdminSettings({ ...adminSettings, integration_close_mode: e.target.value }))
                                .catch(() => setMsg('Failed to update close mode'))
                        }}>
                            <option value="archive">archive</option>
                            <option value="delete">delete</option>
                        </select>
                    </div>
                    <div>Default sync interval (s): {adminSettings.default_sync_interval_seconds}</div>
                    {providerCaps && (
                        <div style={{ marginTop: 8 }}>
                            <div><strong>Provider concurrency caps</strong> (default: {providerCaps.default})</div>
                            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginTop: 6 }}>
                                {Object.keys(providerCaps.caps || {}).map(p => (
                                    <div key={p}>
                                        <label>{p}: </label>
                                        <input type="number" min="1" defaultValue={providerCaps.caps[p]} onBlur={(e) => {
                                            const v = parseInt(e.target.value || '0', 10)
                                            const caps = { ...(providerCaps.caps || {}), [p]: v }
                                            api('/v1/admin/provider_caps', { method: 'POST', body: { caps } })
                                                .then(() => setProviderCaps({ ...providerCaps, caps }))
                                                .catch(() => setMsg('Failed to update caps'))
                                        }} style={{ width: 80 }} />
                                    </div>
                                ))}
                                <div>
                                    <label>Add provider: </label>
                                    <input placeholder="provider" id="prov-name" />
                                    <input placeholder="cap" type="number" min="1" id="prov-cap" style={{ width: 80, marginLeft: 6 }} />
                                    <button onClick={() => {
                                        const name = document.getElementById('prov-name').value.trim()
                                        const cap = parseInt(document.getElementById('prov-cap').value || '0', 10)
                                        if (!name || cap <= 0) return
                                        const caps = { ...(providerCaps.caps || {}), [name]: cap }
                                        api('/v1/admin/provider_caps', { method: 'POST', body: { caps } })
                                            .then(() => setProviderCaps({ ...providerCaps, caps }))
                                            .catch(() => setMsg('Failed to update caps'))
                                    }} style={{ marginLeft: 6 }}>Add/Update</button>
                                </div>
                            </div>
                        </div>
                    )}
                    {orchestration && (
                        <div style={{ marginTop: 8 }}>
                            <div><strong>Orchestration</strong></div>
                            <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                                <button onClick={refreshOrchestration}>Refresh</button>
                                <label>
                                    <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} /> Auto refresh
                                </label>
                                <label>
                                    every <input type="number" min="3" style={{ width: 60 }} value={refreshIntervalSec} onChange={(e) => setRefreshIntervalSec(parseInt(e.target.value || '10', 10))} /> s
                                </label>
                                {orchLoading && <span style={{ color: '#666', fontSize: 12 }}>Refreshing…</span>}
                            </div>
                            <table style={{ borderCollapse: 'collapse', width: '100%', marginTop: 6 }}>
                                <thead>
                                    <tr>
                                        <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', cursor: 'pointer' }} onClick={() => toggleSort('provider')}>Provider {sortKey === 'provider' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th>
                                        <th style={{ textAlign: 'right', borderBottom: '1px solid #ddd', cursor: 'pointer' }} onClick={() => toggleSort('inflight')}>In-flight {sortKey === 'inflight' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th>
                                        <th style={{ textAlign: 'right', borderBottom: '1px solid #ddd', cursor: 'pointer' }} onClick={() => toggleSort('queue')}>Queue Depth {sortKey === 'queue' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th>
                                        <th style={{ textAlign: 'right', borderBottom: '1px solid #ddd', cursor: 'pointer' }} onClick={() => toggleSort('cap')}>Cap {sortKey === 'cap' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(() => {
                                        const rows = [...(orchestration.providers || [])]
                                        const toVal = (p, k) => {
                                            if (k === 'provider') return (p.provider || (p.queue ? `RQ ${p.queue}` : '') || '').toLowerCase()
                                            if (k === 'inflight') return Number.isFinite(p.inflight) ? p.inflight : -1
                                            if (k === 'queue') return Number.isFinite(p.queue_depth) ? p.queue_depth : (Number.isFinite(p.rq_length) ? p.rq_length : -1)
                                            if (k === 'cap') return Number.isFinite(p.cap) ? p.cap : -1
                                            return 0
                                        }
                                        rows.sort((a, b) => {
                                            const av = toVal(a, sortKey)
                                            const bv = toVal(b, sortKey)
                                            if (av < bv) return sortDir === 'asc' ? -1 : 1
                                            if (av > bv) return sortDir === 'asc' ? 1 : -1
                                            return 0
                                        })
                                        return rows.map((p, idx) => {
                                            const cap = Number.isFinite(p.cap) ? p.cap : null
                                            const inflight = Number.isFinite(p.inflight) ? p.inflight : null
                                            let badge = null
                                            if (cap && inflight !== null && cap > 0) {
                                                const util = Math.round((inflight / cap) * 100)
                                                let bg = '#e6f4ea', color = '#1e4620'
                                                if (util >= 100) { bg = '#fdecea'; color = '#b71c1c' }
                                                else if (util >= 80) { bg = '#fff4e5'; color = '#8a4500' }
                                                badge = <span style={{ marginLeft: 6, background: bg, color, padding: '1px 6px', borderRadius: 10, fontSize: 12 }}>{util}%</span>
                                            }
                                            return (
                                                <tr key={idx}>
                                                    <td style={{ padding: '4px 0' }}>{p.provider || (p.queue ? `RQ ${p.queue}` : '')} {badge}</td>
                                                    <td style={{ textAlign: 'right' }}>{p.inflight ?? ''}</td>
                                                    <td style={{ textAlign: 'right' }}>{p.queue_depth ?? (p.rq_length ?? '')}</td>
                                                    <td style={{ textAlign: 'right' }}>{p.cap ?? ''}</td>
                                                </tr>
                                            )
                                        })
                                    })()}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
            <h3>Your Integrations</h3>
            {loading && <div>Loading…</div>}
            {error && <div style={{ color: 'crimson' }}>{error}</div>}
            <ul>
                {integrations && integrations.length ? integrations.map(i => (
                    <li key={i.id} style={{ marginBottom: 8 }}>
                        <strong>{i.provider}</strong> — id: {i.id} — user: {i.user_id}
                        <div style={{ display: 'inline-block', marginLeft: 12 }}>
                            <button onClick={() => fetchEvents(i.id)} disabled={loadingId === i.id} style={{ marginRight: 6 }}>Fetch Events</button>
                            <button onClick={() => previewEvents(i.id)} disabled={loadingId === i.id} style={{ marginRight: 6 }}>Preview</button>
                            <button onClick={() => syncIntegration(i.id)} disabled={loadingId === i.id} style={{ marginRight: 6 }}>Sync → Habits</button>
                            <button onClick={() => removeIntegration(i.id)} disabled={loadingId === i.id}>Remove</button>
                            <div style={{ marginTop: 6 }}>
                                <label style={{ marginRight: 6 }}>Sync interval (s):</label>
                                <input type="number" min="60" defaultValue={900} onBlur={(e) => setIntegrationConfig(i.id, { sync_interval_seconds: parseInt(e.target.value || '900', 10) })} />
                            </div>
                            <div style={{ marginTop: 6 }}>
                                <details>
                                    <summary>Hooks</summary>
                                    <small>JSON config for hooks (pre_sync, post_sync).</small>
                                    <div>
                                        <textarea id={`hooks-${i.id}`} rows={6} cols={60} defaultValue={(() => {
                                            try {
                                                const cfg = details[i.id]?.config ? JSON.parse(details[i.id].config) : {}
                                                const hv = cfg.hooks || hooksExample || { pre_sync: [], post_sync: [] }
                                                return JSON.stringify(hv, null, 2)
                                            } catch (e) {
                                                try { return JSON.stringify(hooksExample || { pre_sync: [], post_sync: [] }, null, 2) } catch (_) { }
                                                return '{\n  "pre_sync": [],\n  "post_sync": []\n}'
                                            }
                                        })()} onBlur={(e) => {
                                            let hooks
                                            try { hooks = JSON.parse(e.target.value || '{}') } catch (err) { setMsg('Invalid JSON'); return }
                                            // validate before saving
                                            api('/v1/admin/hooks/validate', { method: 'POST', body: { hooks } }).then((res) => {
                                                if (!res.ok) {
                                                    const errs = (res.errors || [])
                                                    // annotate inline under the textarea
                                                    const el = document.getElementById(`hooks-${i.id}-errors`)
                                                    if (el) el.textContent = errs.join('\n') || 'Hooks failed validation'
                                                    const ta = document.getElementById(`hooks-${i.id}`)
                                                    if (ta) ta.style.border = '1px solid crimson'
                                                    return
                                                }
                                                // clear errors
                                                const el = document.getElementById(`hooks-${i.id}-errors`)
                                                if (el) el.textContent = ''
                                                const ta = document.getElementById(`hooks-${i.id}`)
                                                if (ta) ta.style.border = ''
                                                setIntegrationConfig(i.id, { hooks })
                                            }).catch(() => setMsg('Validation failed'))
                                        }} />
                                        <div id={`hooks-${i.id}-errors`} style={{ color: 'crimson', whiteSpace: 'pre-wrap', marginTop: 4 }}></div>
                                    </div>
                                </details>
                            </div>
                            <div style={{ marginTop: 6, color: '#555' }}>
                                {(() => {
                                    const info = details[i.id]
                                    if (!info) return null
                                    let last = null
                                    try {
                                        const cfg = info.config ? JSON.parse(info.config) : {}
                                        last = cfg.last_sync_at || cfg.github_since || null
                                    } catch (e) { }
                                    return last ? <span>Last sync: {last}</span> : <span>Last sync: n/a</span>
                                })()}
                            </div>
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
