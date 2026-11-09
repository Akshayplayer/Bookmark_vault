import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Add it to backend/.env")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()

def hash_password(password: str)->str:
    return password_hash.hash(password)

def verify_password(plain: str, hashed: str)->bool:
    return password_hash.verify(plain,hashed)

def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# This object does two jobs:
# It reads the header Authorization: Bearer <token> and extracts just the token string. If the header is missing, it automatically returns 401 Not authenticated.
# tokenUrl="login" tells the /docs page where login happens. That's how the Authorize button knows to call your /login route.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


    
# get_current_user runs before a protected route, turns the token the client sent into a real User object, and stops the request with a 401 if it can't. It's a gatekeeper because a route that depends on it only runs when the visitor has passed these checks.
# jwt.decode does the real security work:
# It recomputes the signature using your SECRET_KEY and compares it with the one in the token. A forged or altered token fails.
# It checks exp, so an expired token fails.
# It returns the payload dict. payload["sub"] is the user id you stored when you created the token, and it was saved as a string, so int(...) converts it back.
# algorithms=[ALGORITHM] restricts which signing algorithm is accepted. Always pass this explicitly, which blocks attacks where a token claims to use a weaker algorithm.

# Three different things can go wrong, and they all become the same response:
# jwt.PyJWTError: bad signature, expired, or malformed token.
# KeyError: the token verified, but has no sub.
# ValueError: sub isn't a number, so int() fails.
# One generic message means the caller learns nothing about why it failed.
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        user_id = int(payload["sub"])
        print(user_id)
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user