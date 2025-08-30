import React, { createContext, useContext, useEffect, useState } from 'react'
import { api } from './api'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    // hydrate from /me on app load
    useEffect(() => {
        (async () => {
            try {
                const me = await api('/v1/auth/me')
                if (me && me.email) setUser({ email: me.email, id: me.id, role: me.role })
            } catch { }
        })()
    }, [])

    async function login(email, password) {
        setLoading(true); setError(null)
        try {
            await api('/v1/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
            // minimal: consider querying a /me endpoint; for now, store email
            setUser({ email })
        } catch (e) {
            setError(String(e))
            throw e
        } finally {
            setLoading(false)
        }
    }

    async function signup(email, password) {
        setLoading(true); setError(null)
        try {
            await api('/v1/auth/signup', { method: 'POST', body: JSON.stringify({ email, password }) })
            setUser({ email })
        } catch (e) {
            setError(String(e))
            throw e
        } finally {
            setLoading(false)
        }
    }

    async function logout() {
        try { await api('/v1/auth/logout', { method: 'POST' }) } catch { }
        setUser(null)
    }

    const value = { user, login, signup, logout, loading, error }
    return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export function useAuth() {
    return useContext(AuthCtx)
}
