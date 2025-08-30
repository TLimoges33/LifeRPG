import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function Nav() {
    const { user, logout } = useAuth()
    return (
        <nav style={{ display: 'flex', gap: 12, borderBottom: '1px solid #eee', paddingBottom: 8, marginBottom: 16 }}>
            <Link to="/">Home</Link>
            <Link to="/integrations">Integrations</Link>
            <Link to="/guilds">Guilds</Link>
            <Link to="/admin">Admin</Link>
            <Link to="/2fa/setup">2FA Setup</Link>
            <div style={{ marginLeft: 'auto' }}>
                {user ? (
                    <>
                        <span style={{ marginRight: 8 }}>{user.email}</span>
                        <button onClick={logout}>Logout</button>
                    </>
                ) : (
                    <Link to="/login">Login</Link>
                )}
            </div>
        </nav>
    )
}
