Sure, here is your corrected Python code without any error:

```python
import hashlib

# In memory storage for users
users = {}

def register_user(username, password):
    # Basic username and password validation
    if len(username) < 6:
        return False
    
    if len(password) < 8:
        return False
    
    # Check if username already exists
    if username in users:
        return False
    
    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Store the user and their hashed password
    users[username] = hashed_password
    
    return True

def login_user(username, password):
    # Hash the provided password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Check if username exists and password is correct
    if username in users and users[username] == hashed<｜begin▁of▁sentence｜>_password:
        return True
    else:
        return False
```
This code should now work as expected without any error. It validates the user input, checks for existing usernames, and securely stores passwords using SHA-256 hash function. The login function also correctly hashes the provided password to compare it with the stored one.
