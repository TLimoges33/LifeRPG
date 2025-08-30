def test_metrics_endpoint_exposes_counters(client):
    # trigger a request so counters increment
    r1 = client.get('/health')
    assert r1.status_code == 200
    m = client.get('/metrics')
    assert m.status_code == 200
    text = m.text
    assert '# HELP http_requests_total' in text
    assert 'http_requests_total{method="GET",path="/health",status="200"}' in text
    assert '# HELP http_request_duration_seconds' in text