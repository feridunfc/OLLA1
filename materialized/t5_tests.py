```python
def test_get_current_user_valid_token():
    from flask import Flask, request
    from jwt import encode, decode

    app = Flask(__name__)
    SECRET_KEY = 'your-secret-key'

    @app.route('/me', methods=['GET'])
    def get_current_user():
        token = request.headers.get('Authorization')
        if not token:
            return {"error": "No token provided"}, 401
        
        try:
            payload = decode(token, SECRET_KEY)
            user_id = payload['user_id']
            return {"user_id": user_id}, 200
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401

    with app.test_client() as client:
        # Create a valid JWT token
        payload = {'user_id': '123'}
        token = encode(payload, SECRET_KEY)
        
        # Make a GET request to /me with the valid token in the Authorization header
        response = client.get('/me', headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        assert response.json == {'user_id': '123'}

def test_get_current_user_missing_token():
    from flask import Flask, request

    app = Flask(__name__)

    @app.route('/me', methods=['GET'])
    def get_current_user():
        token = request.headers.get('Authorization')
        if not token:
            return {"error": "No token provided"}, 401
        
        try:
            payload = decode(token, SECRET_KEY)
            user_id = payload['user_id']
            return {"user_id": user_id}, 200
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401

    with app.test_client() as client:
        # Make a GET request to /me without the Authorization header
        response = client.get('/me')
        
        assert response.status_code == 401
        assert response.json == {'error': 'No token provided'}

def test_get_current_user_invalid_token():
    from flask import Flask, request

    app = Flask(__name__)

    @app.route('/me', methods=['GET'])
    def get_current_user():
        token = request.headers.get('Authorization')
        if not token:
            return {"error": "No token provided"}, 401
        
        try:
            payload = decode(token, SECRET_KEY)
            user_id = payload['user_id']
            return {"user_id": user_id}, 200
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}, 401
