
from fastapi import FastAPI, HTTPException, status, Depends
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut
from app.auth import USERS, hash_password, verify_password, create_access_token, get_current_user

app = FastAPI(title="JWT Auth Minimal")

@app.post("/register", status_code=201)
def register(body: RegisterRequest):
    if body.username in USERS:
        raise HTTPException(status_code=400, detail="User exists")
    USERS[body.username] = {"username": body.username, "password_hash": hash_password(body.password)}
    return {"ok": True}

@app.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = USERS.get(body.username)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")
    token = create_access_token(body.username)
    return TokenResponse(access_token=token)

@app.get("/me", response_model=UserOut)
def me(current = Depends(get_current_user)):
    return UserOut(username=current["username"])
