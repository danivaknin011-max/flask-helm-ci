import pytest
from app import app  # ייבוא של אובייקט ה-Flask מהקובץ app.py

@pytest.fixture
def client():
    # הגדרת מצב בדיקה (Testing mode)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """בדיקה שהדף הראשי (/) מחזיר תשובה תקינה"""
    response = client.get('/')
    assert response.status_code == 200
    # אם יש לך טקסט מסוים ב-index.html, אתה יכול לבדוק שהוא מופיע:
    # assert b"Welcome" in response.data 

def test_prometheus_metrics(client):
    """בדיקה שנקודת הקצה של המטריקות עובדת (בגלל prometheus_client)"""
    response = client.get('/metrics')
    assert response.status_code == 200