# tools/fix_and_materialize.py
import json, os, re, sys, textwrap
from pathlib import Path

WORKDIR = Path(sys.argv[1] if len(sys.argv) > 1 else "./workdir")
OUTDIR  = Path(sys.argv[2] if len(sys.argv) > 2 else "./materialized")
PROJECT = Path(sys.argv[3] if len(sys.argv) > 3 else "./jwt_fastapi_app")

OUTDIR.mkdir(parents=True, exist_ok=True)
PROJECT.mkdir(parents=True, exist_ok=True)
(APP := PROJECT/"app").mkdir(exist_ok=True)
(TESTS := PROJECT/"tests").mkdir(parents=True, exist_ok=True)

def strip_markdown_fences(s: str) -> str:
    if not isinstance(s, str): return ""
    # ```lang\n ... \n```
    s = re.sub(r"^```[a-zA-Z0-9_+-]*\s*", "", s.strip())
    s = re.sub(r"\s*```$", "", s.strip())
    return s

def drop_leading_prose(s: str) -> str:
    """İlk gerçek kod satırından önceki açıklamaları at."""
    if not s: return s
    lines = s.splitlines()
    code_start = 0
    CODE_HINT = re.compile(r"^\s*(from |import |class |def |@|#\!|app\s*=|if __name__|async def|FastAPI|pytest|passlib|jwt)")
    for i, ln in enumerate(lines):
        if CODE_HINT.search(ln):
            code_start = i
            break
    return "\n".join(lines[code_start:]).strip()

def looks_like_flask(s: str) -> bool:
    return "from flask" in s or "Flask(" in s or "flask_" in s

def sanitize(code: str) -> str:
    code = strip_markdown_fences(code or "")
    code = drop_leading_prose(code)
    return code

def write_file(p: Path, content: str):
    p.write_text(content.rstrip() + "\n", encoding="utf-8")

# 1) results.json oku
data = json.loads((WORKDIR/"results.json").read_text(encoding="utf-8"))

# 2) Her task için code/tests’i temizleyip OUTDIR’e dök
execu = data.get("execution", {})
log = []
for tid, payload in execu.items():
    code  = sanitize(payload.get("code", ""))
    tests = sanitize(payload.get("tests", ""))

    # Flask ise uyar, yazma
    if looks_like_flask(code) or looks_like_flask(tests):
        log.append(f"[{tid}] Flask tespit edildi -> atlandı")
        continue

    if code:
        write_file(OUTDIR / f"{tid.lower()}_code.py", code)
        log.append(f"[{tid}] code yazıldı")
    if tests:
        write_file(OUTDIR / f"{tid.lower()}_tests.py", tests)
        log.append(f"[{tid}] tests yazıldı")

# 3) Çalışan minimal FastAPI + JWT iskeleti oluştur (gereksinimlere birebir)
schemas_py = """
from pydantic import BaseModel, Field

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    username: str
"""
auth_py = """
import os, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

USERS = {}  # in-memory

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

SECRET = os.getenv("SECRET", "dev-secret")
ALGO = "HS256"
ACCESS_EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN", "30"))

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(sub: str) -> str:
    now = datetime.utcnow()
    exp = now + timedelta(minutes=ACCESS_EXPIRE_MIN)
    payload = {"sub": sub, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    payload = decode_token(creds.credentials)
    username = payload.get("sub")
    user = USERS.get(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {"username": username}
"""
main_py = """
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
"""
tests_py = """
import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app

@pytest.mark.asyncio
async def test_register_login_me_happy_path():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/register", json={"username":"alice","password":"secret123"})
        assert r.status_code in (201, 200)
        r = await ac.post("/login", json={"username":"alice","password":"secret123"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        r = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "alice"

@pytest.mark.asyncio
async def test_login_fail_and_me_unauthorized():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/login", json={"username":"bob","password":"x"})
        assert r.status_code == status.HTTP_401_UNAUTHORIZED
        r = await ac.get("/me")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED
"""

write_file(APP/"schemas.py", schemas_py)
write_file(APP/"auth.py",    auth_py)
write_file(APP/"main.py",    main_py)
write_file(TESTS/"test_auth.py", tests_py)

# 4) Basit requirements (varsa ezmez)
req = PROJECT/"requirements.txt"
if not req.exists():
    write_file(req, "\n".join([
        "fastapi",
        "uvicorn",
        "passlib[bcrypt]",
        "PyJWT",
        "httpx",
        "pytest",
        "pytest-asyncio"
    ]))

# 5) Log yaz
write_file(OUTDIR/"_sanitize_log.txt", "\n".join(log) or "no items")

print("✅ Temizlik tamam: ", OUTDIR)
print("✅ Minimal proje yazıldı: ", PROJECT)
print("👉 Uygulama: uvicorn app.main:app --reload  (çalışma dizini: jwt_fastapi_app)")
print("👉 Testler : pytest -q                     (çalışma dizini: jwt_fastapi_app)")
