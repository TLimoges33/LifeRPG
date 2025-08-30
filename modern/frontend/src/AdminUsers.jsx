import React, { useState, useEffect } from 'react'

export default function AdminUsers() {
    const [users, setUsers] = useState([])
    const [msg, setMsg] = useState(null)

    useEffect(() => {
        fetch('/api/v1/admin/users', { credentials: 'include' }).then(r => r.json()).then(setUsers).catch(() => setUsers([]))
    }, [])

    function setRole(id, role) {
        fetch(`/api/v1/admin/users/${id}/role`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role }) })
            .then(r => r.json()).then(() => setMsg('Role updated'))
            .catch(() => setMsg('Failed'))
    }

    return (
        <div style={{ marginTop: 20 }}>
            <h2>Admin: Users</h2>
            {msg && <div style={{ color: '#0366d6' }}>{msg}</div>}
            <ul>
                {users && users.length ? users.map(u => (
                    <li key={u.id}>{u.email} — {u.role} <button onClick={() => setRole(u.id, 'moderator')} style={{ marginLeft: 8 }}>Make Moderator</button> <button onClick={() => setRole(u.id, 'admin')} style={{ marginLeft: 8 }}>Make Admin</button></li>
                )) : <li>No users</li>}
            </ul>
        </div>
    )
}
