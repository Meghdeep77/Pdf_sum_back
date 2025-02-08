from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True)
    subscription = Column(Boolean, nullable=False, default=False)
    tokens_used = Column(Integer, nullable=False, default=0)
    free_trial_used = Column(Boolean, nullable=False, default=False)
    uses = Column(Integer, nullable=False, default=0)


    # Define relationship with the User table
    user = relationship("User", back_populates="subscription")


# Update User table to include a relationship
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship with Subscription table
    transactions = relationship("Transaction", back_populates="user")
    subscription = relationship("Subscription", back_populates="user", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    merchant_transaction_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with User Table
    user = relationship("User", back_populates="transactions")