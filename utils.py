from passlib.hash import bcrypt

import jsons
import base64
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session
from starlette import status

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from database import Base, engine, SessionLocal
from models import User,Subscription
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def update_tokens(user_id: int, tokens: int, db: Session):

    # Query the subscription for the given user_id
    subscription = db.query(Subscription).filter(Subscription.id == user_id).first()

    # If no subscription found for the user, return None
    if not subscription:
        return None

    # Add the tokens to the existing tokens_used
    subscription.tokens_used += tokens

    # Commit the transaction to update the database
    db.commit()


def calculate_sha256_string(input_string):
    # Create a hash object using the SHA-256 algorithm
    sha256 = hashes.Hash(hashes.SHA256(), backend=default_backend())
    # Update hash with the encoded string
    sha256.update(input_string.encode('utf-8'))
    # Return the hexadecimal representation of the hash
    return sha256.finalize().hex()
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def base64_encode(input_dict):
    # Convert the dictionary to a JSON string
    json_data = jsons.dumps(input_dict)
    # Encode the JSON string to bytes
    data_bytes = json_data.encode('utf-8')
    # Perform Base64 encoding and return the result as a string
    return base64.b64encode(data_bytes).decode('utf-8')
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def hash_password(password):
    return bcrypt.hash(password)

