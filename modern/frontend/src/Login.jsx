import React, { useState } from 'react'
import { useAuth } from './AuthContext'

export default function Login() {
    const [email, setEmail] = useState('')
    const [pw, setPw] = useState('')
    const [msg, setMsg] = useState(null)
    const { login, signup, loading, error } = useAuth()

    async function doLogin(e) {
        e.preventDefault()
        try { await login(email, pw); setMsg('Logged in') } catch { setMsg('Login failed') }
    }

    async function doSignup(e) {
        e.preventDefault()
        try { await signup(email, pw); setMsg('Signed up') } catch { setMsg('Signup failed') }
    }

    return (
        <div style={{ marginTop: 20 }}>
            <h2>Login / Signup</h2>
            <form onSubmit={doLogin}>
                <div><input placeholder="email" value={email} onChange={e => setEmail(e.target.value)} /></div>
                <div><input placeholder="password" type="password" value={pw} onChange={e => setPw(e.target.value)} /></div>
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <button type="submit" disabled={loading}>Login</button>
                    <button onClick={doSignup} disabled={loading}>Signup</button>
                </div>
            </form>
            {msg && <div style={{ marginTop: 8 }}>{msg}</div>}
            {error && <div style={{ marginTop: 8, color: 'crimson' }}>{error}</div>}
        </div>
    )
}
