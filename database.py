from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace these with your MySQL database details
DATABASE_URL = "mysql+mysqlconnector://root:meghdeep@localhost:3306/fastapi_db"

# Database engine
engine = create_engine(DATABASE_URL)

# Session for database interaction
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()
print("Success")