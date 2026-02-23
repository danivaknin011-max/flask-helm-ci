import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_balance(client):
    """בדיקה שה-API של היתרה מחזיר נתונים בפורמט JSON"""
    response = client.get('/balance')
    assert response.status_code == 200
    data = response.get_json()
    assert 'balance' in data

def test_metrics_endpoint(client):
    """בדיקה שנקודת הניטור של Prometheus עובדת"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'http_requests_total' in response.data