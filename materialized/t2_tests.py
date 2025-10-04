```python
def test_register_user_valid_input():
    assert register_user("john_doe", "password123") == True

def test_register_user_short_username():
    assert register_user("joh", "password123") == False

def test_register_user_short_password():
    assert register_user("john_doe", "passw") == False

def test_register_user_existing_username():
    assert register_user("john_doe", "password123") == False
    assert register_user("jane_doe", "password456") == True

def test_login_user_valid_credentials():
    register_user("john_doe", "password123")
    assert login_user("john_doe", "password123") == True

def test_login_user_invalid_password():
    register_user("john_doe", "password123")
    assert login_user("john_doe", "wrongpassword") == False

def test_login_user_nonexistent_username():
    assert login_user("john_doe", "password123") == False
```
