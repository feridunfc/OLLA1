def test_create_token():
    user_id = 123
    token = create_token(user_id)
    assert 'user_id' in token.decode()
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    assert decoded_token['user_id'] == user_id
    assert 'exp' in decoded_token

def test_verify_valid_token():
    user_id = 123
    token = create_token(user_id)
    result = verify_token(token)
    assert result == user_id

def test_verify_expired_token():
    user_id = 123
    # Create a token that has already expired
    token = create_token(user_id)
    old_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=6)
    with unittest.mock.patch('datetime.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = old_time
        result = verify_token(token)
    assert result == 'Token expired'

def test_verify_invalid_token():
    invalid_token = "invalid_jwt_token"
    result = verify_token(invalid_token)
    assert result == 'Invalid token'
