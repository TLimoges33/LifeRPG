def test_security_headers_present(client):
    r = client.get('/health')
    assert r.status_code == 200
    # core headers always present
    assert r.headers.get('X-Content-Type-Options') == 'nosniff'
    assert r.headers.get('X-Frame-Options') == 'DENY'
    assert r.headers.get('Referrer-Policy') == 'no-referrer'
    assert r.headers.get('Permissions-Policy') == 'geolocation=()'
    assert 'Content-Security-Policy' in r.headers


def test_cors_preflight(client):
    # Simulate a preflight request from allowed origin
    headers = {
        'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type,authorization'
    }
    r = client.options('/api/v1/hello', headers=headers)
    assert r.status_code in (200, 204)
    assert r.headers.get('access-control-allow-origin') == 'http://localhost:5173'
    assert r.headers.get('access-control-allow-credentials') == 'true'


def test_headers_on_other_routes(client):
    # simple GET route
    r = client.get('/api/v1/hello')
    assert r.status_code == 200
    assert r.headers.get('X-Frame-Options') == 'DENY'
    # POST route
    r2 = client.post('/api/v1/users', json={'email': 'h@test'})
    assert r2.status_code in (200, 400)  # email required in some contexts; just check headers presence
    assert 'Content-Security-Policy' in r2.headers


def test_request_size_limit(client):
    # Build a body > 1MiB (default limit)
    big = 'x' * (1024 * 1024 + 1)
    r = client.post('/api/v1/users', data=big, headers={'content-type': 'text/plain'})
    assert r.status_code == 413
    assert r.json().get('detail') == 'request entity too large'


def test_rate_limit_basic(client):
    # Hit a lightweight endpoint enough times to trip limiter quickly by reducing RPM via env is harder in this fixture.
    # Instead, we assume default 120; we'll just assert headers exist for now and simulate close to limit by making a few calls.
    for _ in range(3):
        r = client.get('/api/v1/hello')
        assert r.status_code == 200
        assert 'X-RateLimit-Limit' in r.headers
        assert 'X-RateLimit-Remaining' in r.headers