import pytest
def test_list_integrations_empty(client):
    resp = client.get('/api/v1/integrations')
    assert resp.status_code == 200
