import pytest
import redis
from flask import session
from modules.main import server, app, redis_client, load_credentials

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

# Fake credentials for testing
@pytest.fixture
def fake_credentials(monkeypatch):
    fake_creds = {
        "user1": {
            "username": "admin",
            "password": "adminpassword",
            "group": "0"
        },
        "user2": {
            "username": "testuser",
            "password": "testpassword",
            "group": "1"
        }
    }
    # Rebuild the dictionaries exactly like the code does in main.py
    test_user_pwd = {v['username']: v['password'] for v in fake_creds.values()}
    test_user_groups = {v['username']: v['group'] for v in fake_creds.values()}

    # Patch them in the main module
    monkeypatch.setattr('modules.main.USER_PWD', test_user_pwd)
    monkeypatch.setattr('modules.main.USER_GROUPS', test_user_groups)
    return fake_creds


def test_login_page(client, fake_credentials):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Username:' in response.data
    assert b'Password:' in response.data

def test_successful_login(client, fake_credentials):
    response = client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)
    
    assert response.status_code == 200

def test_unsuccessful_login(client, fake_credentials):
    response = client.post('/login', data=dict(
        username='wronguser',
        password='wrongpassword'
    ))
    
    assert response.status_code == 401

def test_logout(client, fake_credentials):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['group'] = '1'
    
    response = client.get('/logout', follow_redirects=True)
    
    assert response.status_code == 200

def test_rate_limiting(client):
    for _ in range(10):
        response = client.post('/login', data=dict(
            username='testuserd',
            password='testpasswordd'
        ))
    
    assert response.status_code == 429