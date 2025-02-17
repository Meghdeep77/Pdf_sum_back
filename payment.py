import os

import requests
import shortuuid
from fastapi.params import Form
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse,RedirectResponse
import uuid
from fastapi import FastAPI, Request, HTTPException
import hashlib
import base64
import json
import utils
from database import SessionLocal
from dotenv import load_dotenv
load_dotenv()
SALTKEY = os.getenv("SALTKEY")
MERCHANT_ID = os.getenv("MERCHANT_ID")
print(SALTKEY)

from models import Transaction, User, Subscription


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
router = APIRouter()



@router.get("/home", response_class=HTMLResponse)
async def home():
    try:
        with open("Home.html", "r") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@router.post("/phone")
def pay(user_id: str = Form(...), db: Session = Depends(get_db)):
    merchant_transaction_id = shortuuid.uuid()
    user_id = int(user_id)

    new_transaction = Transaction(
        user_id=user_id,
        merchant_transaction_id=merchant_transaction_id,
        amount=10000,
        status="PENDING"
    )
    db.add(new_transaction)
    db.commit()

    MAINPAYLOAD = {
        "merchantId": MERCHANT_ID,
        "merchantTransactionId": merchant_transaction_id,
        "merchantUserId": str(user_id),
        "amount": 10000,
        "redirectUrl": "https://pdf.defmogu.in/status",
        "redirectMode": "REDIRECT",
        "callbackUrl": "http://127.0.0.1:8080/pay/callback",
        "mobileNumber": "9999999999",
        "paymentInstrument": {"type": "PAY_PAGE"},
    }

    # Generate checksum
    INDEX = "1"
    ENDPOINT = "/pg/v1/pay"

    base64String = utils.base64_encode(MAINPAYLOAD)
    mainString = base64String + ENDPOINT + SALTKEY
    sha256Val = utils.calculate_sha256_string(mainString)
    checkSum = sha256Val + '###' + INDEX

    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checkSum,
        'accept': 'application/json',
    }
    json_data = {'request': base64String}

    response = requests.post('https://api.phonepe.com/apis/hermes/pg/v1/pay',
                             headers=headers, json=json_data)
    responseData = response.json()
    print(responseData)

    # Return the redirect URL instead of RedirectResponse
    url = responseData['data']['instrumentResponse']['redirectInfo']['url']
    return {"payment_url": url}  # 🔹 Return JSON




@router.post("/status")
async def get_payment_status(
        user_id: str = Form(...),
        db: Session = Depends(get_db)
):
    try:
        user_id = int(user_id)

        # Fetch the latest transaction for the given user
        transaction = db.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).first()

        if not transaction:
            raise HTTPException(status_code=404, detail="No transactions found for this user")

        merchant_transaction_id = transaction.merchant_transaction_id
        print(merchant_transaction_id)

        # Fetch real-time transaction status from PhonePe
        status_response = utils.check_transaction_status(str(merchant_transaction_id))
        print(status_response)

        transaction_status = status_response.get("data", {}).get("state")
        if not transaction_status:
            raise HTTPException(status_code=400, detail="Invalid response from PhonePe")

        if transaction_status == "COMPLETED":
            print("Here")
            subscription = db.query(Subscription).filter_by(id=user_id).first()  # Fetch user instance
            if subscription:
                subscription.subscription = True  # Update field

        # Update transaction status in the database
        transaction.status = transaction_status
        db.commit()  # Commit the transaction

        return {"transaction_id": merchant_transaction_id, "status": transaction_status}

    except Exception as e:
        return {"status": "error", "message": str(e)}



