```python
def test_register_user(client):
    response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 200
    assert b'"message": "User testuser created"' in response.data

def test_invalid_register_missing_username(client):
    response = client.post('/register', json={'password': 'testpass'})
    assert response.status_code == 400
    assert b'"error": "Missing username or password"' in response.data

def test_invalid_register_missing_password(client):
    response = client.post('/register', json={'username': 'testuser'})
    assert response.status_code == 400
    assert b'"error": "Missing username or password"' in response.data

def test_login_valid_user(client, registered_user):
    response = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 200
    assert b'"access_token":' in response.data

def test_login_invalid_username(client):
    response = client.post('/login', json={'username': 'invaliduser', 'password': 'testpass'})
    assert response.status_code == 401
    assert b'"error": "Invalid username or password"' in response.data

def test_login_invalid_password(client, registered_user):
    response = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
    assert response.status_code == 401
    assert b'"error": "Invalid username or password"' in response.data
```
