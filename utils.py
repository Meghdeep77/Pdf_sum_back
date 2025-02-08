from passlib.hash import bcrypt

import jsons
import base64
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session
from starlette import status

from fastapi import APIRouter, Depends
import hashlib
from database import Base, engine, SessionLocal
from models import User,Subscription

PHONEPE_BASE_URL = "https://api-preprod.phonepe.com/apis/pg-sandbox"
SALT_KEY = "96434309-7796-489d-8924-ab56988a6076"
SALT_INDEX = "1"
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def get_access(user_id: int,  db: Session):

    # Query the subscription for the given user_id
    subscription = db.query(Subscription).filter(Subscription.id == user_id).first()

    # If no subscription found for the user, return None
    if not subscription:
        return None

    # Add the tokens to the existing tokens_used
    is_sub = subscription.subscription
    no_of_uses = subscription.uses

    if is_sub or no_of_uses < 2:
        return "True"
    else:
        return "False"


def get_sub(user_id: int, db: Session):
    # Query the subscription for the given user_id
    subscription = db.query(Subscription).filter(Subscription.id == user_id).first()

    # If no subscription found for the user, return None
    if not subscription:
        return None

    # Add the tokens to the existing tokens_used
    is_sub = subscription.subscription


    if is_sub :
        return "True"
    else:
        return "False"


# Commit the transaction to update the database


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
    return
def update_uses(user_id: int, tokens: int, db: Session):

    # Query the subscription for the given user_id
    subscription = db.query(Subscription).filter(Subscription.id == user_id).first()

    # If no subscription found for the user, return None
    if not subscription:
        return None

    # Add the tokens to the existing tokens_used
    subscription.uses += 1

    # Commit the transaction to update the database
    db.commit()
    return


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

def check_transaction_status( merchant_transaction_id: str):
    try:
        merchant_id: str = "PGTESTPAYUAT86"
        # Construct the URL with Merchant ID & Transaction ID
        url = f"{PHONEPE_BASE_URL}/pg/v1/status/{merchant_id}/{merchant_transaction_id}"

        # Generate the X-VERIFY checksum
        data_to_hash = f"/pg/v1/status/{merchant_id}/{merchant_transaction_id}{SALT_KEY}"
        sha256_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()
        checksum = f"{sha256_hash}###{SALT_INDEX}"

        # Set headers
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-VERIFY": checksum
        }

        # Send GET request to check transaction status
        response = requests.get(url, headers=headers)
        response_data = response.json()

        # Return the response
        return response_data

    except Exception as e:
        return {"error": str(e)}

