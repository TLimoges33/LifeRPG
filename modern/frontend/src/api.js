const API_BASE = import.meta.env.VITE_API_BASE || '/api'

function getCookie(name) {
    if (typeof document === 'undefined') return null
    const match = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()\[\]\\\/\+^])/g, '\\$1') + '=([^;]*)'))
    return match ? decodeURIComponent(match[1]) : null
}

export async function api(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) }
    // If not using Bearer and we have a csrf token cookie, send header for double-submit pattern
    const hasBearer = Object.keys(headers).some(k => k.toLowerCase() === 'authorization' && String(headers[k]).toLowerCase().startsWith('bearer '))
    const csrf = getCookie('csrf_token')
    if (!hasBearer && csrf) headers['X-CSRF-Token'] = csrf

    const res = await fetch(`${API_BASE}${path}`, {
        credentials: 'include',
        headers,
        ...opts,
    })
    const ct = res.headers.get('content-type') || ''
    const body = ct.includes('application/json') ? await res.json() : await res.text()
    if (!res.ok) throw new Error(typeof body === 'string' ? body : body?.detail || res.statusText)
    return body
}
