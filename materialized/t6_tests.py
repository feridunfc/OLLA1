```python
def test_read_users_me_valid_token():
    from fastapi.testclient import TestClient

    app = FastAPI()
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[str]:
        if token == 'fake-super-secret-token':
            return "John Doe"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    app.add_api_route("/me", read_users_me, methods=["GET"], dependencies=[Depends(get_current_user)])

    client = TestClient(app)

    response = client.get("/me", headers={"Authorization": "Bearer fake-super-secret-token"})
    assert response.status_code == 200
    assert response.json() == {"user": "John Doe"}

def test_read_users_me_invalid_token():
    from fastapi.testclient import TestClient

    app = FastAPI()
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[str]:
        if token == 'fake-super-secret-token':
            return "John Doe"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    app.add_api_route("/me", read_users_me, methods=["GET"], dependencies=[Depends(get_current_user)])

    client = TestClient(app)

    response = client.get("/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
```
