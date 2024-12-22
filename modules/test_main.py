import pytest
import redis
from flask import session
from modules.main import server, app, redis_client

@pytest.fixture
def client():
    with server.test_client() as client:
        with server.app_context():
            yield client

def test_redis_connection():
    try:
        redis_client.ping()
        assert True
    except redis.ConnectionError:
        assert False, "Failed to connect to Redis"

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Username:' in response.data
    assert b'Password:' in response.data

def test_successful_login(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['group'] = '1'
    
    response = client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Welcome User!' in response.data

def test_unsuccessful_login(client):
    response = client.post('/login', data=dict(
        username='wronguser',
        password='wrongpassword'
    ))
    
    assert response.status_code == 401
    assert b'Invalid credentials' in response.data

def test_logout(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['group'] = '1'
    
    response = client.get('/logout', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'You are not logged in. Please login at' in response.data

def test_display_page_not_logged_in(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'You are not logged in. Please login at' in response.data

def test_display_page_admin(client):
    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['group'] = '0'
    
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome Admin!' in response.data

def test_display_page_user(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['group'] = '1'
    
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome User!' in response.data

