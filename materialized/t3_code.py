import jwt
import datetime

# Secret key for signing the token
SECRET_KEY = 'YOUR_SECRET_KEY'

def create_token(user_id):
    """Creates a JWT with user id as payload"""
    
    # Set expiration time to 5 minutes from now
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    
    # Create the token
    token = jwt.encode({'user_id': user_id, 'exp': exp}, SECRET<｜begin▁of▁sentence｜>KET, algorithm="HS256")
    
    return token

def verify_token(token):
    """Verifies a JWT"""
    
    try:
        # Decode the token
        decoded = jwt.decode(token, SECRET<｜begin▁of▁sentence｜>KET, algorithms=["HS256"])
        
        return decoded['user_id']
    except jwt.exceptions.ExpiredSignatureError:
        return 'Token expired'
    except jwt.exceptions.InvalidTokenError:
        return 'Invalid token'
```
Please replace `'YOUR_SECRET_KEY'` with your actual secret key. This should be kept secure and not shared publicly. In a real-world application, you would want to use a more secure method for storing this secret key.
