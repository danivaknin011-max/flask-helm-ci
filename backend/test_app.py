import pytest
from unittest.mock import MagicMock, patch
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# אנחנו עושים "Mock" לפונקציה שמתחברת למסד הנתונים
@patch('app.get_db_connection')
def test_get_balance(mock_get_db, client):
    """בדיקה שה-API של היתרה מחזיר נתונים בלי צורך ב-DB אמיתי"""
    
    # יוצרים מצב שבו ה-DB כאילו מחזיר לנו תוצאה
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {'balance': 1000}
    mock_conn.cursor.return_value = mock_cursor
    mock_get_db.return_value = mock_conn

    response = client.get('/balance')
    assert response.status_code == 200
    data = response.get_json()
    assert 'balance' in data
    assert data['balance'] == 1000

def test_metrics_endpoint(client):
    """בדיקה שנקודת הניטור של Prometheus עובדת"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'http_requests_total' in response.data