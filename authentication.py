from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta

from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

import utils
from database import Base, engine, SessionLocal
from models import User

# Constants
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    username: str
    password: str
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Pydantic model for token response
class Token(BaseModel):
    access_token: str
    token_type: str

# Router instance
router = APIRouter()

# Function to authenticate user
db: Session = Depends(get_db)
def authenticate_user(username: str, password: str, db: Session):
    # Query the database for the user
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password):
        return None
    return user

# Function to create JWT token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Login endpoint
@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest, db: Session = Depends(get_db)
):
    user = authenticate_user( login_data.username, login_data.password,db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username,"id":user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.get("/user/me")
async def get_current_user(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        id = payload.get("id")
        print(username, id)
        access = utils.get_access(int(id),db)
        sub = utils.get_sub(int(id),db)
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username , "id": id, "access" : access, "sub": sub}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate token")