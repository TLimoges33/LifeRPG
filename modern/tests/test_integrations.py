import pytest
from fastapi.testclient import TestClient
from modern.backend.app import app

client = TestClient(app)

def test_list_integrations_empty():
    resp = client.get('/api/v1/integrations')
    assert resp.status_code == 200
*** End Patch
