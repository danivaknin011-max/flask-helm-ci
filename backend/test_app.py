import pytest
from unittest.mock import MagicMock, patch
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.get_db_connection')
def test_get_balance(mock_get_db, client):
    # סימולציה של מסד הנתונים
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # אנחנו מגדירים שה-DB יחזיר ערך כלשהו
    mock_cursor.fetchone.return_value = {'balance': 100.0}
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db.return_value = mock_conn

    response = client.get('/balance')
    assert response.status_code == 200
    data = response.get_json()
    assert 'balance' in data
    # אנחנו בודקים שזה מספר, לא משנה איזה
    assert float(data['balance']) == 100.0

def test_metrics_endpoint(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'bank_total_balance_amount' in response.data